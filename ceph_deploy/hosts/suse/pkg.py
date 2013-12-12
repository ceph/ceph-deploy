from ceph_deploy.util import pkg_managers


def install(distro, packages):
    return pkg_managers.zypper(
        distro.conn,
        packages
    )


def remove(distro, packages):
    return pkg_managers.zypper_remove(
        distro.conn,
        packages
    )
