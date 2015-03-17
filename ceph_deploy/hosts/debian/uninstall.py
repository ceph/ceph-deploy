from ceph_deploy.util import pkg_managers


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        'radosgw',
        ]
    pkg_managers.apt_remove(
        conn,
        packages,
        purge=purge,
    )
