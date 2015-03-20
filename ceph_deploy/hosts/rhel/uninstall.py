from ceph_deploy.util import pkg_managers


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        'ceph-common',
        'ceph-mon',
        'ceph-osd',
        'radosgw'
        ]

    pkg_managers.yum_remove(
        conn,
        packages,
    )

    pkg_managers.yum_clean(conn)
