from ceph_deploy.util import paths
from ceph_deploy import conf
from ceph_deploy.lib import remoto
from ceph_deploy.util import constants
from ceph_deploy.util import system


def ceph_version(conn):
    """
    Log the remote ceph-version by calling `ceph --version`
    """
    return remoto.process.run(conn, ['ceph', '--version'])


def mon_create(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    logger = distro.conn.logger
    logger.debug('remote hostname: %s' % hostname)
    path = paths.mon.path(args.cluster, hostname)
    uid = distro.conn.remote_module.path_getuid(constants.base_path)
    gid = distro.conn.remote_module.path_getgid(constants.base_path)
    done_path = paths.mon.done(args.cluster, hostname)
    init_path = paths.mon.init(args.cluster, hostname, distro.init)

    conf_data = conf.ceph.load_raw(args)

    # write the configuration file
    distro.conn.remote_module.write_conf(
        args.cluster,
        conf_data,
        args.overwrite_conf,
    )

    # if the mon path does not exist, create it
    distro.conn.remote_module.create_mon_path(path, uid, gid)

    logger.debug('checking for done path: %s' % done_path)
    if not distro.conn.remote_module.path_exists(done_path):
        logger.debug('done path does not exist: %s' % done_path)
        if not distro.conn.remote_module.path_exists(paths.mon.constants.tmp_path):
            logger.info('creating tmp path: %s' % paths.mon.constants.tmp_path)
            distro.conn.remote_module.makedir(paths.mon.constants.tmp_path)
        keyring = paths.mon.keyring(args.cluster, hostname)

        logger.info('creating keyring file: %s' % keyring)
        distro.conn.remote_module.write_monitor_keyring(
            keyring,
            monitor_keyring,
            uid, gid,
        )

        user_args = []
        if uid != 0:
            user_args = user_args + [ '--setuser', str(uid) ]
        if gid != 0:
            user_args = user_args + [ '--setgroup', str(gid) ]

        remoto.process.run(
            distro.conn,
            [
                'ceph-mon',
                '--cluster', args.cluster,
                '--mkfs',
                '-i', hostname,
                '--keyring', keyring,
            ] + user_args
        )

        logger.info('unlinking keyring file %s' % keyring)
        distro.conn.remote_module.unlink(keyring)

    # create the done file
    distro.conn.remote_module.create_done_path(done_path, uid, gid)

    # create init path
    distro.conn.remote_module.create_init_path(init_path, uid, gid)

    # start mon service
    start_mon_service(distro, args.cluster, hostname)


def mon_add(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    logger = distro.conn.logger
    path = paths.mon.path(args.cluster, hostname)
    uid = distro.conn.remote_module.path_getuid(constants.base_path)
    gid = distro.conn.remote_module.path_getgid(constants.base_path)
    monmap_path = paths.mon.monmap(args.cluster, hostname)
    done_path = paths.mon.done(args.cluster, hostname)
    init_path = paths.mon.init(args.cluster, hostname, distro.init)

    conf_data = conf.ceph.load_raw(args)

    # write the configuration file
    distro.conn.remote_module.write_conf(
        args.cluster,
        conf_data,
        args.overwrite_conf,
    )

    # if the mon path does not exist, create it
    distro.conn.remote_module.create_mon_path(path, uid, gid)

    logger.debug('checking for done path: %s' % done_path)
    if not distro.conn.remote_module.path_exists(done_path):
        logger.debug('done path does not exist: %s' % done_path)
        if not distro.conn.remote_module.path_exists(paths.mon.constants.tmp_path):
            logger.info('creating tmp path: %s' % paths.mon.constants.tmp_path)
            distro.conn.remote_module.makedir(paths.mon.constants.tmp_path)
        keyring = paths.mon.keyring(args.cluster, hostname)

        logger.info('creating keyring file: %s' % keyring)
        distro.conn.remote_module.write_monitor_keyring(
            keyring,
            monitor_keyring,
            uid, gid,
        )

        # get the monmap
        remoto.process.run(
            distro.conn,
            [
                'ceph',
                '--cluster', args.cluster,
                'mon',
                'getmap',
                '-o',
                monmap_path,
            ],
        )

        # now use it to prepare the monitor's data dir
        user_args = []
        if uid != 0:
            user_args = user_args + [ '--setuser', str(uid) ]
        if gid != 0:
            user_args = user_args + [ '--setgroup', str(gid) ]

        remoto.process.run(
            distro.conn,
            [
                'ceph-mon',
                '--cluster', args.cluster,
                '--mkfs',
                '-i', hostname,
                '--monmap',
                monmap_path,
                '--keyring', keyring,
            ] + user_args
        )

        logger.info('unlinking keyring file %s' % keyring)
        distro.conn.remote_module.unlink(keyring)

    # create the done file
    distro.conn.remote_module.create_done_path(done_path, uid, gid)

    # create init path
    distro.conn.remote_module.create_init_path(init_path, uid, gid)

    # start mon service
    start_mon_service(distro, args.cluster, hostname)


def map_components(notsplit_packages, components):
    """
    Returns a list of packages to install based on component names

    This is done by checking if a component is in notsplit_packages,
    if it is, we know we need to install 'ceph' instead of the
    raw component name.  Essentially, this component hasn't been
    'split' from the master 'ceph' package yet.
    """
    packages = set()

    for c in components:
        if c in notsplit_packages:
            packages.add('ceph')
        else:
            packages.add(c)

    return list(packages)


def start_mon_service(distro, cluster, hostname):
    """
    start mon service depending on distro init
    """
    if distro.init == 'sysvinit':
        service = distro.conn.remote_module.which_service()
        remoto.process.run(
            distro.conn,
            [
                service,
                'ceph',
                '-c',
                '/etc/ceph/{cluster}.conf'.format(cluster=cluster),
                'start',
                'mon.{hostname}'.format(hostname=hostname)
            ],
            timeout=7,
        )
        system.enable_service(distro.conn)

    elif distro.init == 'upstart':
        remoto.process.run(
             distro.conn,
             [
                 'initctl',
                 'emit',
                 'ceph-mon',
                 'cluster={cluster}'.format(cluster=cluster),
                 'id={hostname}'.format(hostname=hostname),
             ],
             timeout=7,
         )

    elif distro.init == 'systemd':
       # enable ceph target for this host (in case it isn't already enabled)
        remoto.process.run(
            distro.conn,
            [
                'systemctl',
                'enable',
                'ceph.target'
            ],
            timeout=7,
        )

        # enable and start this mon instance
        remoto.process.run(
            distro.conn,
            [
                'systemctl',
                'enable',
                'ceph-mon@{hostname}'.format(hostname=hostname),
            ],
            timeout=7,
        )
        remoto.process.run(
            distro.conn,
            [
                'systemctl',
                'start',
                'ceph-mon@{hostname}'.format(hostname=hostname),
            ],
            timeout=7,
        )
