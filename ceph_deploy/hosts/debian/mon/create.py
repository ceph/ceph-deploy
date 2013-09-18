from ceph_deploy.hosts import common
from ceph_deploy.misc import remote_shortname
from ceph_deploy.lib.remoto import process
from ceph_deploy.connection import get_connection


def create(distro, logger, args, monitor_keyring):
    hostname = remote_shortname(distro.sudo_conn.modules.socket)
    common.mon_create(distro, logger, args, monitor_keyring, hostname)

    distro.sudo_conn.close()
    # TODO transition this once pushy is out
    rconn = get_connection(hostname, logger)

    if distro.init == 'upstart':  # Ubuntu uses upstart
        process.run(
            rconn,
            [
                'initctl',
                'emit',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=args.cluster),
                'id={hostname}'.format(hostname=hostname),
            ],
            exit=True,
            timeout=7,
        )

    elif distro.init == 'sysvinit':  # Debian uses sysvinit
        service = common.which_service(distro.sudo_conn, logger)

        process.run(
            rconn,
            [
                service,
                'ceph',
                'start',
                'mon.{hostname}'.format(hostname=hostname)
            ],
            exit=True,
            timeout=7,
        )
    else:
        raise RuntimeError('create cannot use init %s' % distro.init)
