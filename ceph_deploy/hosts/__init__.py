"""
We deal (mostly) with remote hosts. To avoid special casing each different
commands (e.g. using `yum` as opposed to `apt`) we can make a one time call to
that remote host and set all the special cases for running commands depending
on the type of distribution/version we are dealing with.
"""
import logging
from ceph_deploy import lsb, exc
from ceph_deploy.util import wrappers, pkg_managers
from ceph_deploy.sudo_pushy import get_transport
from ceph_deploy.hosts import debian, centos, fedora, suse

# Import sudo_pushy and patch it
import pushy
from ceph_deploy import sudo_pushy
sudo_pushy.patch()
logger = logging.getLogger()


def get(hostname, fallback=None):
    """
    Retrieve the module that matches the distribution of a ``hostname``. This
    function will connect to that host and retrieve the distribution
    informaiton, then return the appropriate module and slap a few attributes
    to that module defining the information it found from the hostname.

    For example, if host ``node1.example.com`` is an Ubuntu server, the
    ``debian`` module would be returned and the following would be set::

        module.name = 'ubuntu'
        module.release = '12.04'
        module.codename = 'precise'

    :param hostname: A hostname that is reachable/resolvable over the network
    :param fallback: Optional fallback to use if no supported distro is found
    """
    sudo_conn = pushy.connect(get_transport(hostname))
    if not has_lsb(sudo_conn):
        logger.warning('lsb_release was not found - attempting to install')
        install_lsb(sudo_conn)

    (distro, release, codename) = lsb.get_lsb_release(sudo_conn)

    module = _get_distro(distro)
    module.name = distro
    module.release = release
    module.codename = codename
    module.sudo_conn = sudo_conn
    module.init = lsb.choose_init(distro, codename)
    return module


def has_lsb(conn):
    stdout, stderr, _ = wrappers.Popen(conn, logger, ['which', 'lsb_release'])
    return stderr == ''


def install_lsb(conn):
    distro, release, codename = conn.modules.platform.linux_distribution()
    package_manager = detect_package_manager(distro)

    if package_manager == 'yum' and distro.lower() in ['centos', 'scientific']:
        logger.info('adding EPEL repository')
        if float(release) >= 6:
            wrappers.check_call(conn, logger, [
                'wget',
                'http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm',],
                stop_on_error=False,
            )
            pkg_managers.rpm(conn, logger,
                ['epel-release-6*.rpm'],
                stop_on_error=False,
            )
        else:
            wrappers.check_call(conn, logger, [
                'wget',
                'wget http://dl.fedoraproject.org/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm',],
                stop_on_error=False,
            )
            pkg_managers.rpm(conn, logger,
                ['epel-release-5*.rpm'],
                stop_on_error=False,
            )
        pkg_managers.yum(conn, logger, 'redhat-lsb-core')
    elif package_manager == 'apt':
        pkg_managers.apt(conn, logger, 'lsb-release')
    else:
        raise RuntimeError('package lsb_release could not be installed')


def detect_package_manager(distro):
    pkg_managers = {
        'ubuntu': 'apt',
        'debian': 'apt',
        'centos': 'yum',
        'scientific': 'yum',
        'redhat': 'yum',
    }
    return pkg_managers.get(distro.lower())


def _get_distro(distro, fallback=None):
    distro = _normalized_distro_name(distro)
    distributions = {
        'debian': debian,
        'ubuntu': debian,
        'centos': centos,
        'scientific': centos,
        'redhat': centos,
        'fedora': fedora,
        'suse': suse,
        }
    try:
        return distributions[distro]
    except KeyError:
        if fallback:
            return _get_distro(fallback)
        raise exc.UnsupportedPlatform(distro=distro, codename='')


def _normalized_distro_name(distro):
    distro = distro.lower()
    if distro.startswith('redhat'):
        return 'redhat'
    elif distro.startswith('suse'):
        return 'suse'
    return distro
