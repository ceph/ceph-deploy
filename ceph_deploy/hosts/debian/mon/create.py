from ceph_deploy.hosts import common
from ceph_deploy.util import system
from ceph_deploy.lib import remoto


def create(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    common.mon_create(distro, args, monitor_keyring, hostname)

    if distro.init == 'sysvinit':
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
    elif distro.init == 'upstart':
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
