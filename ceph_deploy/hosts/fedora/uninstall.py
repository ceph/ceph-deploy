from ceph_deploy.util import pkg_managers


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        ]

    pkg_managers.yum_remove(
        conn,
        packages,
    )

