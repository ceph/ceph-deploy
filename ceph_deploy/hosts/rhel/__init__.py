from . import mon  # noqa
from .install import install, mirror_install, repo_install  # noqa
from .uninstall import uninstall  # noqa
from ceph_deploy.util import pkg_managers
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
        return 'sysvinit'

    if not module.conn.remote_module.path_exists("/usr/lib/systemd/system/ceph.target"):
        return 'sysvinit'

    if is_systemd(module.conn):
        return 'systemd'

    return 'systemd'

def get_packager(module):
    return pkg_managers.Yum(module)
