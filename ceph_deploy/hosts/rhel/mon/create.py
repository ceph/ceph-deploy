from ceph_deploy.hosts import common
from ceph_deploy.util import system
from ceph_deploy.lib import remoto


def create(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    common.mon_create(distro, args, monitor_keyring, hostname)
    service = distro.conn.remote_module.which_service()

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

    system.enable_service(distro.conn)
