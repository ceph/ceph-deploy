from . import mon  # noqa
from .install import install, mirror_install, repo_install  # noqa
from .uninstall import uninstall  # noqa
import logging

from ceph_deploy.util import pkg_managers, init_systems

# Allow to set some information about this distro
#

log = logging.getLogger(__name__)

distro = None
release = None
codename = None

def choose_init(module):
    """
    Select a init system

    Returns the name of a init system (upstart, sysvinit ...).
    """
    init_mapping = { '11' : init_systems.SysV, # SLE_11
        '12' : init_systems.SystemD,               # SLE_12
        '13.1' : init_systems.SystemD,             # openSUSE_13.1
        }
    return init_mapping.get(release, init_systems.SystemD)(module)


def get_packager(module):
    return pkg_managers.Zypper(module)
