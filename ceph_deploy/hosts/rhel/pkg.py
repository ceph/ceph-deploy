from ceph_deploy.util import pkg_managers


def install(distro, packages):
    return pkg_managers.yum(
        distro.conn,
        packages
    )


def remove(distro, packages):
    return pkg_managers.yum_remove(
        distro.conn,
        packages
    )
