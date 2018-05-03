from . import mon  # noqa
from .install import install  # noqa
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

    Returns the name of a init system (systemd, sysvinit ...).
    """


    if is_systemd(module.conn):
        return 'systemd'

    return 'sysvinit'


def get_packager(module):
    return pkg_managers.AptRpm(module)
