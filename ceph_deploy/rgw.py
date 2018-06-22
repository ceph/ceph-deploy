import errno
import logging
import os

from ceph_deploy import conf
from ceph_deploy import exc
from ceph_deploy import hosts
from ceph_deploy.util import system
from ceph_deploy.lib import remoto
from ceph_deploy.cliutil import priority
from ceph_deploy import validate


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


def rgw_duplicate_port_check(cfg):
    all_sections = cfg.sections()
    host_port_mapping = {}
    for section in all_sections:
        if cfg.has_option(section, 'host') is False:
            continue
        if cfg.has_option(section, 'rgw_frontends') is False:
            continue
        host = cfg.get(section, 'host')
        rgw_frontends = cfg.get(section, 'rgw_frontends')
        port_num = None
        for option in rgw_frontends.split(' '):
            options_split = option.split('=')
            if len(options_split) < 2:
                continue
            if options_split[0].strip() == 'port':
                port_str = options_split[1].strip()
                try:
                    port_num = int(port_str)
                except:
                    continue
        if port_num is None:
            continue
        old_num = host_port_mapping.get(host)
        if old_num == None:
           host_port_mapping[host] = port_num
           continue
        if old_num == port_num:
            LOG.warning('Duplicate services for port %s on host %s.' % (port_num, host))
            return True
    return False


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
    for hostname, name, port in args.rgw:
        if not name.startswith('rgw.'):
            msg = "rgw name '%s' does not start with 'rgw.'" % (name)
            LOG.error(msg)
            raise RuntimeError(msg)
        enitity = 'client.{name}'.format(name=name)
        if cfg.has_section(enitity) is False:
            cfg.add_section(enitity)
            changed_cfg = True
        else:
            # We have existing confg for the rgw
            LOG.warning("existing configuration for rgw %s:%s" % (hostname, name))
        if cfg.has_option(enitity,'host') is False:
            cfg.set(enitity, 'host', hostname)
            changed_cfg = True
        else:
            existing_value = cfg.get(enitity, 'host')
            if existing_value != hostname:
                msg = "exisiting rgw '%s:%s' has a different hostname" % (hostname, name)
                LOG.error(msg)
                raise RuntimeError(msg)
        if cfg.has_option(enitity,'rgw_dns_name') is False:
            cfg.set(enitity, 'rgw_dns_name', hostname)
            changed_cfg = True
        else:
            existing_value = cfg.get(enitity, 'rgw_dns_name')
            if existing_value != hostname:
                msg = "exisiting rgw '%s:%s' has a different rgw_dns_name" % (hostname, name)
                LOG.error(msg)
                raise RuntimeError(msg)
        rgw_frontends_value = "civetweb port=%s" % (port)
        if cfg.has_option(enitity,'rgw frontends') is False:
            # TODO this should be customizable
            cfg.set(enitity, 'rgw frontends', rgw_frontends_value)
            changed_cfg = True
        else:
            existing_value = cfg.get(enitity, 'rgw frontends')
            if existing_value != rgw_frontends_value:
                msg = "exisiting rgw '%s:%s' has a different 'rgw frontends'" % (hostname, name)
                LOG.error(msg)
                raise RuntimeError(msg)

    # If config file is changed save changes locally
    if changed_cfg is True:
        cfg_path = args.ceph_conf or '{cluster}.conf'.format(cluster=args.cluster)
        if rgw_duplicate_port_check(cfg):
            msg = "Refusing to modify config file '%s' as it would have duplicate a port" % (cfg_path)
            LOG.error(msg)
            raise RuntimeError(msg)
        if args.overwrite_conf is False:
            msg = "The local config file '%s' exists with content that must be changed; use --overwrite-conf to update" % (cfg_path)
            LOG.error(msg)
            raise RuntimeError(msg)
        with open(cfg_path, 'wb') as configfile:
            cfg.write(configfile)

    for hostname, name, port in args.rgw:
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
                 'port %s'),
                hostname,
                port
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


def rgw_stop(conn, name, cluster, init):
    if init == 'upstart':
        remoto.process.run(
            conn,
            [
                'initctl',
                'stop',
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
                'stop',
            ],
            timeout=7
        )
    elif init == 'systemd':
        remoto.process.run(
            conn,
            [
                'systemctl',
                'disable',
                'ceph-radosgw@{name}'.format(name=name),
            ],
            timeout=7
        )
        remoto.process.run(
            conn,
            [
                'systemctl',
                'stop',
                'ceph-radosgw@{name}'.format(name=name),
            ],
            timeout=7
        )


def rgw_delete(args):
    cfg = conf.ceph.load(args)
    LOG.debug(
        'Deploying rgw, cluster %s hosts %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.rgw),
        )
    errors = 0

    # Check if config needs to be changed
    changed_cfg = False
    for hostname, name, port in args.rgw:
        enitity = 'client.{name}'.format(name=name)
        if cfg.has_section(enitity) is True:
            cfg.remove_section(enitity)
            changed_cfg = True

    # If config file will be changed
    if changed_cfg is True:
        cfg_path = args.ceph_conf or '{cluster}.conf'.format(cluster=args.cluster)
        if args.overwrite_conf is False:
            msg = "The local config file '%s' exists with content that must be changed; use --overwrite-conf to update" % (cfg_path)
            LOG.error(msg)
            raise RuntimeError(msg)

    changed_cfg = False

    for hostname, name, port in args.rgw:
        try:
            distro = hosts.get(hostname, username=args.username)
            LOG.info(
                'Distro info: %s %s %s',
                distro.name,
                distro.release,
                distro.codename
            )
            LOG.debug('remote host will use %s', distro.init)
            rgw_stop(distro.conn, name, args.cluster, distro.init)
            path = '/var/lib/ceph/radosgw/{cluster}-{name}'.format(
                cluster=args.cluster,
                name=name
            )
            if distro.conn.remote_module.path_exists(path):
                LOG.info("Found path %s" % (path))
                files_to_del = distro.conn.remote_module.listdir(path)
                for file_name in files_to_del:
                    file_path = os.path.join(path, file_name)
                    distro.conn.remote_module.unlink(file_path)
            else:
                LOG.info("Path '%s' not found"  % (path))

            distro.conn.exit()
            enitity = 'client.{name}'.format(name=name)
            if cfg.has_section(enitity) is True:
                cfg.remove_section(enitity)
            changed_cfg = True
            LOG.info('The Ceph Object Gateway (RGW) is deleted from host %s' % (hostname))
        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    # If config file has been changed
    if changed_cfg is True:
        cfg_path = args.ceph_conf or '{cluster}.conf'.format(cluster=args.cluster)
        with open(cfg_path, 'wb') as configfile:
            cfg.write(configfile)
        # now distribute
        for hostname, name, port in args.rgw:
            try:
                distro = hosts.get(hostname, username=args.username)
                LOG.info(
                    'Distro info: %s %s %s',
                    distro.name,
                    distro.release,
                    distro.codename
                )
                conf_data = conf.ceph.load_raw(args)
                distro.conn.remote_module.write_conf(
                    args.cluster,
                    conf_data,
                    args.overwrite_conf,
                )

            except RuntimeError as e:
                LOG.error(e)
                errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d RGWs' % errors)


def rgw(args):
    if args.subcommand == 'create':
        return rgw_create(args)
    if args.subcommand == 'list':
        return rgw_list(args)
    if args.subcommand == 'delete':
        return rgw_delete(args)
    LOG.error('subcommand %s not implemented', args.subcommand)


def colon_separated(s):
    host = s
    name = 'rgw.' + s
    port = '7480'
    delimiter_count = s.count(':')
    if delimiter_count == 1:
        (host, name) = s.split(':')
    if delimiter_count == 2:
        (host, name, port) = s.split(':')
    name = validate.alphanumericdot(name)
    return (host, name, port)


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
        metavar='HOST[:NAME][:PORT]',
        nargs='+',
        type=colon_separated,
        help='host (and optionally the daemon name and port) to deploy on.',
        )
    rgw_parser.add_parser(
        'list',
        help='list all rgw instances in local config'
        )
    rgw_delete = rgw_parser.add_parser(
        'delete',
        help='Create a rgw instance'
        )
    rgw_delete.add_argument(
        'rgw',
        metavar='HOST[:NAME]',
        nargs='+',
        type=colon_separated,
        help='host (and optionally the daemon name) to deploy on.',
        )
    parser.set_defaults(
        func=rgw,
        )
