import mon  # noqa
import pkg  # noqa
from install import install, mirror_install, repo_install  # noqa
from uninstall import uninstall  # noqa
import logging

# Allow to set some information about this distro
#

log = logging.getLogger(__name__)

distro = None
release = None
codename = None

def choose_init():
    """
    Select a init system

    Returns the name of a init system (upstart, sysvinit ...).
    """
    init_mapping = { '11' : 'sysvinit', # SLE_11
        '12' : 'systemd',               # SLE_12
        '13.1' : 'systemd',             # openSUSE_13.1
        }
    return init_mapping.get(release, 'sysvinit')
