from ceph_deploy.hosts import common
from ceph_deploy.lib import remoto


def create(distro, args, monitor_keyring):
    logger = distro.conn.logger
    hostname = distro.conn.remote_module.shortname()
    common.mon_create(distro, args, monitor_keyring, hostname)
    service = distro.conn.remote_module.which_service()

    if not service:
        logger.warning('could not find `service` executable')

    if distro.init == 'upstart':  # Ubuntu uses upstart
        remoto.process.run(
            distro.conn,
            [
                'initctl',
                'emit',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=args.cluster),
                'id={hostname}'.format(hostname=hostname),
            ],
            timeout=7,
        )

    elif distro.init == 'sysvinit':  # Debian uses sysvinit

        remoto.process.run(
            distro.conn,
            [
                service,
                'ceph',
                '-c',
                '/etc/ceph/{cluster}.conf'.format(cluster=args.cluster),
                'start',
                'mon.{hostname}'.format(hostname=hostname)
            ],
            timeout=7,
        )
    else:
        raise RuntimeError('create cannot use init %s' % distro.init)
