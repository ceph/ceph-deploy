import logging

from ceph_deploy.util.system import disable_service, stop_service
from ceph_deploy.lib import remoto


SYSTEMD_UNITS = [
    'ceph-mds.target',
    'ceph-mon.target',
    'ceph-osd.target',
    'ceph-radosgw.target',
    'ceph-fuse.target',
    'ceph-mgr.target',
    'ceph-rbd-mirror.target',
    'ceph.target',
]


def uninstall(distro, purge=False):
    packages = [
        'ceph',
    ]

    hostname = distro.conn.hostname
    LOG = logging.getLogger(hostname)

    # I need to stop and disable services prior package removal
    LOG.info('stopping and disabling services on {}'.format(hostname))
    for unit in SYSTEMD_UNITS:
        stop_service(distro.conn, unit)
        disable_service(distro.conn, unit)

    # remoto.process.run(
    #     distro.conn,
    #     [
    #         'systemctl',
    #         'daemon-reload',
    #     ]
    # )

    LOG.info('uninstalling packages on {}'.format(hostname))
    distro.packager.remove(packages)

    remoto.process.run(
        distro.conn,
        [
            'systemctl',
            'reset-failed',
        ]
    )
