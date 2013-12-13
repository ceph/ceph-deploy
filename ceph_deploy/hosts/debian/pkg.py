from ceph_deploy.util import pkg_managers


def install(distro, packages):
    return pkg_managers.apt(
        distro.conn,
        packages
    )


def remove(distro, packages):
    return pkg_managers.apt_remove(
        distro.conn,
        packages
    )
