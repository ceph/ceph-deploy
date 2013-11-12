"""
We deal (mostly) with remote hosts. To avoid special casing each different
commands (e.g. using `yum` as opposed to `apt`) we can make a one time call to
that remote host and set all the special cases for running commands depending
on the type of distribution/version we are dealing with.
"""
import logging
from ceph_deploy import exc, lsb
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
    conn.import_module(remotes)
    distro_name, release, codename = conn.remote_module.platform_information()
    if not codename:
        raise exc.UnsupportedPlatform(distro=distro_name, codename=codename)

    machine_type = conn.remote_module.machine_type()

    module = _get_distro(distro_name)
    module.name = distro_name
    module.release = release
    module.codename = codename
    module.conn = conn
    module.machine_type = machine_type
    module.init = lsb.choose_init(distro_name, codename)

    return module


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
    if distro.startswith(('redhat', 'red hat')):
        return 'redhat'
    elif  distro.startswith(('scientific', 'scientific linux')):
        return 'scientific'
    elif distro.startswith('suse'):
        return 'suse'
    return distro
