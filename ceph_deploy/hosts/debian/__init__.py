import mon  # noqa
import pkg  # noqa
from install import install, mirror_install, repo_install  # noqa
from uninstall import uninstall  # noqa

# Allow to set some information about this distro
#

distro = None
release = None
codename = None

def choose_init():    
    """
    Select a init system

    Returns the name of a init system (upstart, sysvinit ...).
    """
    if distro.lower() == 'ubuntu':
        return 'upstart'
    return 'sysvinit'
