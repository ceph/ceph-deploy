from ceph_deploy.util import pkg_managers


def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-release',
        'ceph-common',
        'ceph-radosgw',
        ]

    pkg_managers.yum_remove(
        distro.conn,
        packages,
    )

    pkg_managers.yum_clean(distro.conn)
