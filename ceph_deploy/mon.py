import ConfigParser
import logging
import re

from cStringIO import StringIO

from . import conf
from . import exc
from . import lsb
from .cliutil import priority


log = logging.getLogger(__name__)


def write_conf(cluster, conf):
    import os

    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp = '{path}.{pid}.tmp'.format(path=path, pid=os.getpid())

    with file(tmp, 'w') as f:
        f.write(conf)
        f.flush()
        os.fsync(f)
    os.rename(tmp, path)


def create_mon(cluster, monitor_keyring, init):
    import os
    import socket
    import subprocess

    hostname = socket.gethostname()
    path = '/var/lib/ceph/mon/ceph-{hostname}'.format(
        hostname=hostname,
        )
    done_path = '/var/lib/ceph/mon/ceph-{hostname}/done'.format(
        hostname=hostname,
        )
    init_path = '/var/lib/ceph/mon/ceph-{hostname}/{init}'.format(
        hostname=hostname,
        init=init,
        )

    if not os.path.exists(path):
        os.mkdir(path)

    if not os.path.exists(done_path):
        keyring = '/var/lib/ceph/tmp/{cluster}-{hostname}.mon.keyring'.format(
            cluster=cluster,
            hostname=hostname,
            )

        with file(keyring, 'w') as f:
            f.write(monitor_keyring)

        subprocess.check_call(
            args=[
                'ceph-mon',
                '--cluster', cluster,
                '--mkfs',
                '-i', hostname,
                '--keyring', keyring,
                ],
            )
        os.unlink(keyring)
        with file(done_path, 'w'):
            pass

    if not os.path.exists(init_path):
        with file(init_path, 'w'):
            pass

    if init == 'upstart':
        subprocess.check_call(
            args=[
                'initctl',
                'emit',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=cluster),
                'id={hostname}'.format(hostname=hostname),
                ],
            )
    elif init == 'sysvinit':
        subprocess.check_call(
            args=[
                'service',
                'ceph',
                'start',
                'mon.{hostname}'.format(hostname=hostname),
                ],
            )


def mon_create(args):
    cfg = conf.load(args)
    if not args.mon:
        try:
            mon_initial_members = cfg.get('global', 'mon_initial_members')
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            pass
        else:
            args.mon = re.split(r'[,\s]+', mon_initial_members)

    if not args.mon:
        raise exc.NeedHostError()

    try:
        with file('{cluster}.mon.keyring'.format(cluster=args.cluster),
                  'rb') as f:
            monitor_keyring = f.read()
    except IOError:
        raise RuntimeError('mon keyring not found; run \'new\' to create a new cluster')

    log.debug(
        'Deploying mon, cluster %s hosts %s',
        args.cluster,
        ' '.join(args.mon),
        )

    for hostname in args.mon:
        log.debug('Deploying mon to %s', hostname)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))

        lsb_release_r = sudo.compile(lsb.lsb_release)
        (distro, release, codename) = lsb_release_r()
        init = lsb.choose_init(distro, codename)
        log.debug('Distro %s codename %s, will use %s',
                  distro, codename, init)

        write_conf_r = sudo.compile(write_conf)
        conf_data = StringIO()
        cfg.write(conf_data)
        write_conf_r(
            cluster=args.cluster,
            conf=conf_data.getvalue(),
            )

        create_mon_r = sudo.compile(create_mon)
        create_mon_r(
            cluster=args.cluster,
            monitor_keyring=monitor_keyring,
            init=init,
            )

        # TODO add_bootstrap_peer_hint

def mon(args):
    if args.subcommand == 'create':
        mon_create(args)
    else:
        log.error('subcommand %s not implemented', args.subcommand)

@priority(30)
def make(parser):
    """
    Deploy ceph monitor on remote hosts.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'create',
            'destroy',
            ],
        help='create or destroy',
        )
    parser.add_argument(
        'mon',
        metavar='HOST',
        nargs='*',
        help='host to deploy on',
        )
    parser.set_defaults(
        func=mon,
        )
