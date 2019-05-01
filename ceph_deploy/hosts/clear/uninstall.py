import logging

from ceph_deploy.util.system import disable_service, stop_service

SYSTEMD_UNITS = [
    'ceph-mds.target',
    'ceph-mon.target',
    'ceph-osd.target',
    'ceph-radosgw.target',
    'ceph-fuse.target',
    'ceph-mgr.target',
    'ceph-rbd-mirror.target',
    'ceph.target',
    'ceph-mds*service',
    'ceph-mon*service',
    'ceph-osd*service',
    'ceph-radosgw*service',
    'ceph-fuse*service',
    'ceph-mgr*service',
    'ceph-rbd-mirror*service',
    'ceph*service',
]


def uninstall(distro, purge=False):

    hostname = distro.conn.hostname
    LOG = logging.getLogger(hostname)

    # I need to stop and disable services prior package removal
    LOG.info('stopping and disabling services on {}'.format(hostname))
    for unit in SYSTEMD_UNITS:
        stop_service(distro.conn, unit)
        disable_service(distro.conn, unit)

    packages = [
        'storage-cluster',
        'ceph'
        ]

    distro.packager.remove(packages)
    distro.packager.clean()
