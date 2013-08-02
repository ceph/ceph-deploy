from ceph_deploy.util.wrappers import check_call
from ceph_deploy.hosts import common


def create(distro, logger, args, monitor_keyring):
    hostname = distro.sudo_conn.modules.socket.gethostname().split('.')[0]
    common.mon_create(distro, logger, args, monitor_keyring, hostname)

    if distro.name.lower() == 'ubuntu':
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
        )

    else:  # Debian doesn't use initctl
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
        )
