from ceph_deploy.util import paths
from ceph_deploy.util.wrappers import check_call
from ceph_deploy.util.context import remote


def ceph_version(conn, logger):
    """
    Log the remote ceph-version by calling `ceph --version`
    """
    return check_call(conn, logger, ['ceph', '--version'])


def which_service(conn, logger):
    """
    Attempt to find the right `service` executable location as it
    might not be in the path for the user executing the remote
    calls
    """
    locations = ['/sbin/service', '/usr/sbin/service']
    for location in locations:
        if conn.modules.os.path.exists(location):
            return location


def mon_create(distro, logger, args, monitor_keyring, hostname):
    logger.debug('remote hostname: %s' % hostname)
    path = paths.mon.path(args.cluster, hostname)
    done_path = paths.mon.done(args.cluster, hostname)
    init_path = paths.mon.init(args.cluster, hostname, 'sysvinit')

    if not distro.sudo_conn.modules.os.path.exists(path):
        logger.info('creating path: %s' % path)
        distro.sudo_conn.modules.os.makedirs(path)

    logger.debug('checking for done path: %s' % done_path)
    if not distro.sudo_conn.modules.os.path.exists(done_path):
        logger.debug('done path does not exist: %s' % done_path)
        if not distro.sudo_conn.modules.os.path.exists(paths.mon.constants.tmp_path):
            logger.info('creating tmp path: %s' % paths.mon.constants.tmp_path)
            distro.sudo_conn.modules.os.makedirs(paths.mon.constants.tmp_path)
        keyring = paths.mon.keyring(args.cluster, hostname)

        def write_monitor_keyring():
            """create the monitor keyring file"""
            with file(keyring, 'w') as f:
                f.write(monitor_keyring)

        logger.info('creating keyring file: %s' % keyring)
        with remote(distro.sudo_conn, logger, write_monitor_keyring) as remote_func:
            remote_func()

        check_call(
            distro.sudo_conn,
            logger,
            [
                'ceph-mon',
                '--cluster', args.cluster,
                '--mkfs',
                '-i', hostname,
                '--keyring', keyring,
            ],
        )

        logger.info('unlinking keyring file %s' % keyring)
        distro.sudo_conn.modules.os.unlink(keyring)

    def create_done_path(done_path):
        """create a done file to avoid re-doing the mon deployment"""
        with file(done_path, 'w'):
            pass

    with remote(distro.sudo_conn, logger, create_done_path) as remote_func:
        remote_func(done_path)

    def create_init_path(init_path):
        """create the init path if it does not exist"""
        import os
        if not os.path.exists(init_path):
            with file(init_path, 'w'):
                pass

    with remote(distro.sudo_conn, logger, create_init_path) as remote_func:
        remote_func(init_path)
