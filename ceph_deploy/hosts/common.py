from ceph_deploy.util import paths
from ceph_deploy import conf
from ceph_deploy.lib.remoto import process
from StringIO import StringIO


def ceph_version(conn):
    """
    Log the remote ceph-version by calling `ceph --version`
    """
    return process.run(conn, ['ceph', '--version'])


def mon_create(distro, args, monitor_keyring, hostname):
    logger = distro.conn.logger
    logger.debug('remote hostname: %s' % hostname)
    path = paths.mon.path(args.cluster, hostname)
    done_path = paths.mon.done(args.cluster, hostname)
    init_path = paths.mon.init(args.cluster, hostname, distro.init)

    configuration = conf.load(args)
    conf_data = StringIO()
    configuration.write(conf_data)

    # write the configuration file
    distro.conn.remote_module.write_conf(
        args.cluster,
        conf_data.getvalue(),
        args.overwrite_conf,
    )

    # if the mon path does not exist, create it
    distro.conn.remote_module.create_mon_path(path)

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
        )

        process.run(
            distro.conn,
            [
                'ceph-mon',
                '--cluster', args.cluster,
                '--mkfs',
                '-i', hostname,
                '--keyring', keyring,
            ],
        )

        logger.info('unlinking keyring file %s' % keyring)
        distro.conn.remote_module.unlink(keyring)

    # create the done file
    distro.conn.remote_module.create_done_path(done_path)

    # create init path
    distro.conn.remote_module.create_init_path(init_path)
