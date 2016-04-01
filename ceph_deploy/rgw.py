import errno
import logging
import os

from ceph_deploy import conf
from ceph_deploy import exc
from ceph_deploy import hosts
from ceph_deploy.util import system
from ceph_deploy.lib import remoto
from ceph_deploy.cliutil import priority


LOG = logging.getLogger(__name__)


def get_bootstrap_rgw_key(cluster):
    """
    Read the bootstrap-rgw key for `cluster`.
    """
    path = '{cluster}.bootstrap-rgw.keyring'.format(cluster=cluster)
    try:
        with open(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-rgw keyring not found; run \'gatherkeys\'')


def create_rgw(distro, name, cluster, init):
    conn = distro.conn

    path = '/var/lib/ceph/radosgw/{cluster}-{name}'.format(
        cluster=cluster,
        name=name
        )

    conn.remote_module.safe_makedirs(path)

    bootstrap_keyring = '/var/lib/ceph/bootstrap-rgw/{cluster}.keyring'.format(
        cluster=cluster
        )

    keypath = os.path.join(path, 'keyring')

    stdout, stderr, returncode = remoto.process.check(
        conn,
        [
            'ceph',
            '--cluster', cluster,
            '--name', 'client.bootstrap-rgw',
            '--keyring', bootstrap_keyring,
            'auth', 'get-or-create', 'client.{name}'.format(name=name),
            'osd', 'allow rwx',
            'mon', 'allow rw',
            '-o',
            os.path.join(keypath),
        ]
    )
    if returncode > 0 and returncode != errno.EACCES:
        for line in stderr:
            conn.logger.error(line)
        for line in stdout:
            # yes stdout as err because this is an error
            conn.logger.error(line)
        conn.logger.error('exit code from command was: %s' % returncode)
        raise RuntimeError('could not create rgw')

        remoto.process.check(
            conn,
            [
                'ceph',
                '--cluster', cluster,
                '--name', 'client.bootstrap-rgw',
                '--keyring', bootstrap_keyring,
                'auth', 'get-or-create', 'client.{name}'.format(name=name),
                'osd', 'allow *',
                'mon', 'allow *',
                '-o',
                os.path.join(keypath),
            ]
        )

    conn.remote_module.touch_file(os.path.join(path, 'done'))
    conn.remote_module.touch_file(os.path.join(path, init))

    if init == 'upstart':
        remoto.process.run(
            conn,
            [
                'initctl',
                'emit',
                'radosgw',
                'cluster={cluster}'.format(cluster=cluster),
                'id={name}'.format(name=name),
            ],
            timeout=7
        )
    elif init == 'sysvinit':
        remoto.process.run(
            conn,
            [
                'service',
                'ceph-radosgw',
                'start',
            ],
            timeout=7
        )
        if distro.is_el:
            system.enable_service(distro.conn, service='ceph-radosgw')
    elif init == 'systemd':
        remoto.process.run(
            conn,
            [
                'systemctl',
                'enable',
                'ceph-radosgw@{name}'.format(name=name),
            ],
            timeout=7
        )
        remoto.process.run(
            conn,
            [
                'systemctl',
                'start',
                'ceph-radosgw@{name}'.format(name=name),
            ],
            timeout=7
        )
        remoto.process.run(
            conn,
            [
                'systemctl',
                'enable',
                'ceph.target',
            ],
            timeout=7
        )


def rgw_create(args):
    cfg = conf.ceph.load(args)
    LOG.debug(
        'Deploying rgw, cluster %s hosts %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.rgw),
        )

    key = get_bootstrap_rgw_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0

    # Update the config file
    changed_cfg = False
    for hostname, name in args.rgw:
        enitity = 'client.{name}'.format(name=name)
        port = 7480
        if cfg.has_section(enitity) is False:
            cfg.add_section(enitity)
            changed_cfg = True
        if cfg.has_option(enitity,'host') is False:
            cfg.set(enitity, 'host', hostname)
            changed_cfg = True
        if cfg.has_option(enitity,'rgw_dns_name') is False:
            # TODO this should be customizable
            value = "%s:%s" % (hostname,port)
            cfg.set(enitity, 'rgw_dns_name', hostname)
            changed_cfg = True
        if cfg.has_option(enitity,'rgw frontends') is False:
            # TODO this should be customizable
            cfg.set(enitity, 'rgw frontends', "civetweb port=%s" % (port))
            changed_cfg = True

    # If config file is changed save changes locally
    if changed_cfg is True:
        cfg_path = args.ceph_conf or '{cluster}.conf'.format(cluster=args.cluster)
        if args.overwrite_conf is False:
            msg = "The local config file '%s' exists with content that must be changed; use --overwrite-conf to update" % (cfg_path)
            LOG.error(msg)
            raise RuntimeError(msg)
        with open(cfg_path, 'wb') as configfile:
            cfg.write(configfile)

    for hostname, name in args.rgw:
        try:
            distro = hosts.get(hostname, username=args.username)
            rlogger = distro.conn.logger
            LOG.info(
                'Distro info: %s %s %s',
                distro.name,
                distro.release,
                distro.codename
            )
            LOG.debug('remote host will use %s', distro.init)

            if hostname not in bootstrapped:
                bootstrapped.add(hostname)
                LOG.debug('deploying rgw bootstrap to %s', hostname)
                conf_data = conf.ceph.load_raw(args)
                distro.conn.remote_module.write_conf(
                    args.cluster,
                    conf_data,
                    args.overwrite_conf,
                )

                path = '/var/lib/ceph/bootstrap-rgw/{cluster}.keyring'.format(
                    cluster=args.cluster,
                )

                if not distro.conn.remote_module.path_exists(path):
                    rlogger.warning('rgw keyring does not exist yet, creating one')
                    distro.conn.remote_module.write_keyring(path, key)

            create_rgw(distro, name, args.cluster, distro.init)
            distro.conn.exit()
            LOG.info(
                ('The Ceph Object Gateway (RGW) is now running on host %s and '
                 'default port %s'),
                hostname,
                '7480'
            )
        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d RGWs' % errors)


def rgw_list(args):
    cfg = conf.ceph.load(args)
    for rgw_section in cfg.sections():
        host = cfg.safe_get(rgw_section, 'host')
        entity = None
        if rgw_section.startswith('client.rgw'):
            entity = rgw_section[7:]
        if rgw_section.startswith('client.radosgw.'):
            entity = rgw_section[7:]
        if entity is None:
            continue
        print ("{host}:{entity}".format(host=host, entity=entity))


def rgw(args):
    if args.subcommand == 'create':
        return rgw_create(args)
    if args.subcommand == 'list':
        return rgw_list(args)
    LOG.error('subcommand %s not implemented', args.subcommand)


def colon_separated(s):
    host = s
    name = s
    if s.count(':') == 1:
        (host, name) = s.split(':')
    name = 'rgw.' + name
    return (host, name)


@priority(30)
def make(parser):
    """
    Ceph RGW daemon management
    """
    rgw_parser = parser.add_subparsers(dest='subcommand')
    rgw_parser.required = True
    rgw_create = rgw_parser.add_parser(
        'create',
        help='Create an RGW instance'
        )
    rgw_create.add_argument(
        'rgw',
        metavar='HOST[:NAME]',
        nargs='+',
        type=colon_separated,
        help='host (and optionally the daemon name) to deploy on. \
                NAME is automatically prefixed with \'rgw.\'',
        )
    rgw_parser.add_parser(
        'list',
        help='list all rgw instances in local config'
        )
    parser.set_defaults(
        func=rgw,
        )
