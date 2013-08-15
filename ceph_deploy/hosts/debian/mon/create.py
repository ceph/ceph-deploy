from ceph_deploy.util.wrappers import check_call
from ceph_deploy.hosts import common


def create(distro, logger, args, monitor_keyring):
    hostname = distro.sudo_conn.modules.socket.gethostname().split('.')[0]
    common.mon_create(distro, logger, args, monitor_keyring, hostname)

    if distro.init == 'upstart': # Ubuntu uses upstart
        check_call(
            distro.sudo_conn,
            logger,
            [
                'initctl',
                'emit',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=args.cluster),
                'id={hostname}'.format(hostname=hostname),
            ],
            patch=False,
        )

    elif distro.init == 'sysvinit': # Debian uses sysvinit
        service = common.which_service(distro.sudo_conn, logger)

        check_call(
            distro.sudo_conn,
            logger,
            [
                service,
                'ceph',
                'start',
                'mon.{hostname}'.format(hostname=hostname)
            ],
            patch=False,
        )
    else:
        raise RuntimeError('create cannot use init %s' % distro.init)
