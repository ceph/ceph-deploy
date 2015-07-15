from ceph_deploy.util import pkg_managers


def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-common',
        'ceph-radosgw',
        ]

    pkg_managers.yum_remove(
        distro.conn,
        packages,
    )

