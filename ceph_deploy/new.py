import errno
import logging
import os
import uuid
import struct
import time
import base64
import socket

from ceph_deploy.cliutil import priority
from ceph_deploy import conf, hosts, exc
from ceph_deploy.util import arg_validators, ssh, net
from ceph_deploy.misc import mon_hosts
from ceph_deploy.lib import remoto
from ceph_deploy.connection import get_local_connection


LOG = logging.getLogger(__name__)


def generate_auth_key():
    key = os.urandom(16)
    header = struct.pack(
        '<hiih',
        1,                 # le16 type: CEPH_CRYPTO_AES
        int(time.time()),  # le32 created: seconds
        0,                 # le32 created: nanoseconds,
        len(key),          # le16: len(key)
    )
    return base64.b64encode(header + key)


def ssh_copy_keys(hostname, username=None):
    LOG.info('making sure passwordless SSH succeeds')
    if ssh.can_connect_passwordless(hostname):
        return

    LOG.warning('could not connect via SSH')

    # Create the key if it doesn't exist:
    id_rsa_pub_file = os.path.expanduser(u'~/.ssh/id_rsa.pub')
    id_rsa_file = id_rsa_pub_file.split('.pub')[0]
    if not os.path.exists(id_rsa_file):
        LOG.info('creating a passwordless id_rsa.pub key file')
        with get_local_connection(LOG) as conn:
            remoto.process.run(
                conn,
                [
                    'ssh-keygen',
                    '-t',
                    'rsa',
                    '-N',
                    "",
                    '-f',
                    id_rsa_file,
                ]
            )

    # Get the contents of id_rsa.pub and push it to the host
    LOG.info('will connect again with password prompt')
    distro = hosts.get(hostname, username, detect_sudo=False)
    auth_keys_path = '.ssh/authorized_keys'
    if not distro.conn.remote_module.path_exists(auth_keys_path):
        distro.conn.logger.warning(
            '.ssh/authorized_keys does not exist, will skip adding keys'
        )
    else:
        LOG.info('adding public keys to authorized_keys')
        with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as id_rsa:
            contents = id_rsa.read()
        distro.conn.remote_module.append_to_file(
            auth_keys_path,
            contents
        )
    distro.conn.exit()


def validate_host_ip(ips, subnets):
    """
    Make sure that a given host all subnets specified will have at least one IP
    in that range.
    """
    # Make sure we prune ``None`` arguments
    subnets = [s for s in subnets if s is not None]
    validate_one_subnet = len(subnets) == 1

    def ip_in_one_subnet(ips, subnet):
        """ ensure an ip exists in at least one subnet """
        for ip in ips:
            if net.ip_in_subnet(ip, subnet):
                return True
        return False

    for subnet in subnets:
        if ip_in_one_subnet(ips, subnet):
            if validate_one_subnet:
                return
            else:  # keep going to make sure the other subnets are ok
                continue
        else:
            msg = "subnet (%s) is not valid for any of the ips found %s" % (subnet, str(ips))
            raise RuntimeError(msg)


def get_public_network_ip(ips, public_subnet):
    """
    Given a public subnet, chose the one IP from the remote host that exists
    within the subnet range.
    """
    for ip in ips:
        if net.ip_in_subnet(ip, public_subnet):
            return ip
    msg = "IPs (%s) are not valid for any of subnet specified %s" % (str(ips), str(public_subnet))
    raise RuntimeError(msg)


def new(args):
    if args.ceph_conf:
        raise RuntimeError('will not create a Ceph conf file if attemtping to re-use with `--ceph-conf` flag')
    LOG.debug('Creating new cluster named %s', args.cluster)
    cfg = conf.ceph.CephConf()
    cfg.add_section('global')

    fsid = args.fsid or uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))

    # if networks were passed in, lets set them in the
    # global section
    if args.public_network:
        cfg.set('global', 'public network', str(args.public_network))

    if args.cluster_network:
        cfg.set('global', 'cluster network', str(args.cluster_network))

    mon_initial_members = []
    mon_host = []

    for (name, host) in mon_hosts(args.mon):
        # Try to ensure we can ssh in properly before anything else
        if args.ssh_copykey:
            ssh_copy_keys(host, args.username)

        # Now get the non-local IPs from the remote node
        distro = hosts.get(host, username=args.username)
        remote_ips = net.ip_addresses(distro.conn)

        # custom cluster names on sysvinit hosts won't work
        if distro.init == 'sysvinit' and args.cluster != 'ceph':
            LOG.error('custom cluster names are not supported on sysvinit hosts')
            raise exc.ClusterNameError(
                'host %s does not support custom cluster names' % host
            )

        distro.conn.exit()

        # Validate subnets if we received any
        if args.public_network or args.cluster_network:
            validate_host_ip(remote_ips, [args.public_network, args.cluster_network])

        # Pick the IP that matches the public cluster (if we were told to do
        # so) otherwise pick the first, non-local IP
        LOG.debug('Resolving host %s', host)
        if args.public_network:
            ip = get_public_network_ip(remote_ips, args.public_network)
        else:
            ip = net.get_nonlocal_ip(host)
        LOG.debug('Monitor %s at %s', name, ip)
        mon_initial_members.append(name)
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            mon_host.append("[" + ip + "]")
            LOG.info('Monitors are IPv6, binding Messenger traffic on IPv6')
            cfg.set('global', 'ms bind ipv6', 'true')
        except socket.error:
            mon_host.append(ip)



    LOG.debug('Monitor initial members are %s', mon_initial_members)
    LOG.debug('Monitor addrs are %s', mon_host)

    cfg.set('global', 'mon initial members', ', '.join(mon_initial_members))
    # no spaces here, see http://tracker.newdream.net/issues/3145
    cfg.set('global', 'mon host', ','.join(mon_host))

    # override undesirable defaults, needed until bobtail

    # http://tracker.ceph.com/issues/6788
    cfg.set('global', 'auth cluster required', 'cephx')
    cfg.set('global', 'auth service required', 'cephx')
    cfg.set('global', 'auth client required', 'cephx')

    path = '{name}.conf'.format(
        name=args.cluster,
        )

    new_mon_keyring(args)

    LOG.debug('Writing initial config to %s...', path)
    tmp = '%s.tmp' % path
    with file(tmp, 'w') as f:
        cfg.write(f)
    try:
        os.rename(tmp, path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            raise exc.ClusterExistsError(path)
        else:
            raise


def new_mon_keyring(args):
    LOG.debug('Creating a random mon key...')
    mon_keyring = '[mon.]\nkey = %s\ncaps mon = allow *\n' % generate_auth_key()

    keypath = '{name}.mon.keyring'.format(
        name=args.cluster,
        )
    oldmask = os.umask(077)
    LOG.debug('Writing monitor keyring to %s...', keypath)
    try:
        tmp = '%s.tmp' % keypath
        with open(tmp, 'w', 0600) as f:
            f.write(mon_keyring)
        try:
            os.rename(tmp, keypath)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise exc.ClusterExistsError(keypath)
            else:
                raise
    finally:
        os.umask(oldmask)


@priority(10)
def make(parser):
    """
    Start deploying a new cluster, and write a CLUSTER.conf and keyring for it.
    """
    parser.add_argument(
        'mon',
        metavar='MON',
        nargs='+',
        help='initial monitor hostname, fqdn, or hostname:fqdn pair',
        type=arg_validators.Hostname(),
        )
    parser.add_argument(
        '--no-ssh-copykey',
        dest='ssh_copykey',
        action='store_false',
        default=True,
        help='do not attempt to copy SSH keys',
    )

    parser.add_argument(
        '--fsid',
        dest='fsid',
        help='provide an alternate FSID for ceph.conf generation',
    )

    parser.add_argument(
        '--cluster-network',
        help='specify the (internal) cluster network',
        type=arg_validators.Subnet(),
    )

    parser.add_argument(
        '--public-network',
        help='specify the public network for a cluster',
        type=arg_validators.Subnet(),
    )

    parser.set_defaults(
        func=new,
        )
