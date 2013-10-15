from ceph_deploy.hosts import common
from ceph_deploy.lib.remoto import process


def create(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    common.mon_create(distro, args, monitor_keyring, hostname)
    service = distro.conn.remote_module.which_service()

    process.run(
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
