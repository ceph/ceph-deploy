from ceph_deploy.util import paths
from ceph_deploy import conf
from ceph_deploy.lib import remoto
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from ceph_deploy.util import constants


def ceph_version(conn):
    """
    Log the remote ceph-version by calling `ceph --version`
    """
    return remoto.process.run(conn, ['ceph', '--version'])


def mon_create(distro, args, monitor_keyring, hostname):
    logger = distro.conn.logger
    logger.debug('remote hostname: %s' % hostname)
    path = paths.mon.path(args.cluster, hostname)
    uid = distro.conn.remote_module.path_getuid(constants.base_path)
    gid = distro.conn.remote_module.path_getgid(constants.base_path)
    done_path = paths.mon.done(args.cluster, hostname)
    init_path = paths.mon.init(args.cluster, hostname, distro.init)

    configuration = conf.ceph.load(args)
    conf_data = StringIO()
    configuration.write(conf_data)

    # write the configuration file
    distro.conn.remote_module.write_conf(
        args.cluster,
        conf_data.getvalue(),
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


def mon_add(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    logger = distro.conn.logger
    path = paths.mon.path(args.cluster, hostname)
    uid = distro.conn.remote_module.path_getuid(constants.base_path)
    gid = distro.conn.remote_module.path_getgid(constants.base_path)
    monmap_path = paths.mon.monmap(args.cluster, hostname)
    done_path = paths.mon.done(args.cluster, hostname)
    init_path = paths.mon.init(args.cluster, hostname, distro.init)

    configuration = conf.ceph.load(args)
    conf_data = StringIO()
    configuration.write(conf_data)

    # write the configuration file
    distro.conn.remote_module.write_conf(
        args.cluster,
        conf_data.getvalue(),
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

    # start the mon using the address
    pid_location = "/var/run/ceph/mon.%s.pid" % hostname
    remoto.process.run(
        distro.conn,
        [
            'ceph-mon',
            '-i',
            hostname,
            '--pid-file', pid_location,
            '--public-addr',
            args.address,
        ],
    )


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
