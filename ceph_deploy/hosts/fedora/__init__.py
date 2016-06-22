from . import mon  # noqa
from ceph_deploy.hosts.centos.install import repo_install  # noqa
from .install import install, mirror_install  # noqa
from .uninstall import uninstall  # noqa
from ceph_deploy.util import pkg_managers

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

    if not module.conn.remote_module.path_exists("/usr/lib/systemd/system/ceph.target"):
        return 'sysvinit'

    return 'systemd'

def get_packager(module):
    if module.normalized_release.int_major >= 22:
        return pkg_managers.DNF(module)
    else:
        return pkg_managers.Yum(module)
