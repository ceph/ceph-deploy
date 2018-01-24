from ceph_deploy.hosts.centos.install import repo_install, mirror_install  # noqa
from ceph_deploy.hosts.common import map_components
from ceph_deploy.util.system import enable_service, start_service


NON_SPLIT_PACKAGES = [
    'ceph-osd',
    'ceph-radosgw',
    'ceph-mds',
    'ceph-mon',
    'ceph-mgr',
    'ceph-common',
    'ceph-test'
]

SYSTEMD_UNITS = [
    'ceph.target',
    'ceph-radosgw.target',
    'ceph-rbd-mirror.target',
    'ceph-fuse.target',
    'ceph-mds.target',
    'ceph-mon.target',
    'ceph-mgr.target',
    'ceph-osd.target',
]
SYSTEMD_UNITS_SKIP_START = [
    'ceph-mgr.target',
    'ceph-mon.target',
]
SYSTEMD_UNITS_SKIP_ENABLE = [
]


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.pop('components', [])
    )

    distro.packager.install(
        packages
    )

    # Start and enable services
    for unit in SYSTEMD_UNITS:
        if unit not in SYSTEMD_UNITS_SKIP_START:
            start_service(distro.conn, unit)
        if unit not in SYSTEMD_UNITS_SKIP_ENABLE:
            enable_service(distro.conn, unit)
