from ceph_deploy.util import pkg_managers
from ceph_deploy.lib.remoto import process


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        ]
    pkg_managers.apt_remove(
        conn,
        packages,
        purge=purge,
    )
