from . import mon # noqa
from .install import install # noqa
from .uninstall import uninstall # noqa
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
    # Currently clearlinux only has systemd.
    return 'systemd'


def get_packager(module):
    return pkg_managers.Swupd(module)
