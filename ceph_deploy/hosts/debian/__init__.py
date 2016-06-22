from . import mon  # noqa
from .install import install, mirror_install, repo_install  # noqa
from .uninstall import uninstall  # noqa
from ceph_deploy.util import pkg_managers
from ceph_deploy.util.system import is_systemd, is_upstart

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
    # Upstart checks first because when installing ceph, the
    # `/lib/systemd/system/ceph.target` file may be created, fooling this
    # detection mechanism.
    if is_upstart(module.conn):
        return 'upstart'

    if is_systemd(module.conn) or module.conn.remote_module.path_exists(
            "/lib/systemd/system/ceph.target"):
        return 'systemd'

    return 'sysvinit'


def get_packager(module):
    return pkg_managers.Apt(module)
