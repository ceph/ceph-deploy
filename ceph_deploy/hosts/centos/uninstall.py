from ceph_deploy.util import pkg_managers
from ceph_deploy.lib.remoto import process


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        ]

    pkg_managers.yum_remove(
        conn,
        packages,
    )
