import mon  # noqa
from install import install, mirror_install, repo_install  # noqa
from uninstall import uninstall  # noqa
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
    # fixme: newer ubuntu runs systemd
    if distro.lower() == 'ubuntu':
        return 'upstart'
    if module.conn.remote_module.path_exists("/lib/systemd/system/ceph.target"):
        return 'systemd'
    return 'sysvinit'


def get_packager(module):
    return pkg_managers.Apt(module)


def service_mapping(service):
    """
    Select the service name
    """
    service_mapping = { }
    return service_mapping.get(service,service)
