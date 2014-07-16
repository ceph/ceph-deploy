from ceph_deploy.util import pkg_managers


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        'ceph-release',
        'ceph-common',
        ]

    pkg_managers.yum_remove(
        conn,
        packages,
    )

    pkg_managers.yum_clean(conn)
