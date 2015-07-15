from ceph_deploy.util import pkg_managers


def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        'radosgw',
        ]
    pkg_managers.apt_remove(
        distro.conn,
        packages,
        purge=purge,
    )
