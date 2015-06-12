from ceph_deploy.util import pkg_managers


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        'ceph-common',
        'libcephfs1',
        'librados2',
        'librbd1',
        'ceph-radosgw',
        ]
    pkg_managers.zypper_remove(conn, packages)
