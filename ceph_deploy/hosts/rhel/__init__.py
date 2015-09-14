from .install import install, mirror_install, repo_install  # noqa
from .uninstall import uninstall  # noqa
from ceph_deploy.util import pkg_managers, init_systems
from ceph_deploy.util.system import is_systemd

# Allow to set some information about this distro
#

distro = None
release = None
codename = None

def choose_init(module):
    """
    Select a init system

    Returns the name of a init system (upstart, sysvinit ...).
    """

    if module.normalized_release.int_major < 7:
        return init_systems.SysV(module)

    if not module.conn.remote_module.path_exists("/usr/lib/systemd/system/ceph.target"):
        return init_systems.SysV(module)

    if is_systemd(module.conn):
        return init_systems.SystemD(module)

    return init_systems.SystemD(module)

def get_packager(module):
    return pkg_managers.Yum(module)
