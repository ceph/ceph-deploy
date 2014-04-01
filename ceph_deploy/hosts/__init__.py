"""
We deal (mostly) with remote hosts. To avoid special casing each different
commands (e.g. using `yum` as opposed to `apt`) we can make a one time call to
that remote host and set all the special cases for running commands depending
on the type of distribution/version we are dealing with.
"""
import logging
from ceph_deploy import exc
from ceph_deploy.hosts import debian, centos, fedora, suse, remotes
from ceph_deploy.connection import get_connection

logger = logging.getLogger()


def get(hostname, username=None, fallback=None):
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
    conn = get_connection(
        hostname,
        username=username,
        logger=logging.getLogger(hostname)
    )
    try:
        conn.import_module(remotes)
    except IOError as error:
        if 'already closed' in getattr(error, 'message', ''):
            raise RuntimeError('remote connection got closed, ensure ``requiretty`` is disabled for %s' % hostname)
    distro_name, release, codename = conn.remote_module.platform_information()
    if not codename or not _get_distro(distro_name):
        raise exc.UnsupportedPlatform(
            distro=distro_name,
            codename=codename,
            release=release)

    machine_type = conn.remote_module.machine_type()

    module = _get_distro(distro_name)
    module.name = distro_name
    module.normalized_name = _normalized_distro_name(distro_name)
    module.release = release
    module.codename = codename
    module.conn = conn
    module.machine_type = machine_type
    module.init = _choose_init(distro_name, codename)

    return module


def _get_distro(distro, fallback=None):
    if not distro:
        return

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

    return distributions.get(distro) or _get_distro(fallback)


def _normalized_distro_name(distro):
    distro = distro.lower()
    if distro.startswith(('redhat', 'red hat')):
        return 'redhat'
    elif distro.startswith(('scientific', 'scientific linux')):
        return 'scientific'
    elif distro.startswith(('suse', 'opensuse')):
        return 'suse'
    return distro


def _choose_init(distro, codename):
    """
    Select a init system for a given distribution.

    Returns the name of a init system (upstart, sysvinit ...).
    """
    if distro == 'Ubuntu':
        return 'upstart'
    return 'sysvinit'
