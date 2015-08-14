"""
We deal (mostly) with remote hosts. To avoid special casing each different
commands (e.g. using `yum` as opposed to `apt`) we can make a one time call to
that remote host and set all the special cases for running commands depending
on the type of distribution/version we are dealing with.
"""
import logging
from ceph_deploy import exc
from ceph_deploy.util import versions
from ceph_deploy.hosts import debian, centos, fedora, suse, remotes, rhel
from ceph_deploy.connection import get_connection

logger = logging.getLogger()


def get(hostname,
        username=None,
        fallback=None,
        detect_sudo=True,
        use_rhceph=False,
        callbacks=None):
    """
    Retrieve the module that matches the distribution of a ``hostname``. This
    function will connect to that host and retrieve the distribution
    information, then return the appropriate module and slap a few attributes
    to that module defining the information it found from the hostname.

    For example, if host ``node1.example.com`` is an Ubuntu server, the
    ``debian`` module would be returned and the following would be set::

        module.name = 'ubuntu'
        module.release = '12.04'
        module.codename = 'precise'

    :param hostname: A hostname that is reachable/resolvable over the network
    :param fallback: Optional fallback to use if no supported distro is found
    :param use_rhceph: Whether or not to install RH Ceph on a RHEL machine or
                       the community distro.  Changes what host module is
                       returned for RHEL.
    :params callbacks: A list of callables that accept one argument (the actual
                       module that contains the connection) that will be
                       called, in order at the end of the instantiation of the
                       module.
    """
    conn = get_connection(
        hostname,
        username=username,
        logger=logging.getLogger(hostname),
        detect_sudo=detect_sudo
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
    module = _get_distro(distro_name, use_rhceph=use_rhceph)
    module.name = distro_name
    module.normalized_name = _normalized_distro_name(distro_name)
    module.normalized_release = _normalized_release(release)
    module.distro = module.normalized_name
    module.is_el = module.normalized_name in ['redhat', 'centos', 'fedora', 'scientific']
    module.is_rpm = module.normalized_name in ['redhat', 'centos',
                                               'fedora', 'scientific', 'suse']
    module.is_deb = not module.is_rpm
    module.release = release
    module.codename = codename
    module.conn = conn
    module.machine_type = machine_type
    module.init = module.choose_init(module)
    module.packager = module.get_packager(module)
    # execute each callback if any
    if callbacks:
        for c in callbacks:
            c(module)
    return module


def _get_distro(distro, fallback=None, use_rhceph=False):
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

    if distro == 'redhat' and use_rhceph:
        return rhel
    else:
        return distributions.get(distro) or _get_distro(fallback)


def _normalized_distro_name(distro):
    distro = distro.lower()
    if distro.startswith(('redhat', 'red hat')):
        return 'redhat'
    elif distro.startswith(('scientific', 'scientific linux')):
        return 'scientific'
    elif distro.startswith(('suse', 'opensuse')):
        return 'suse'
    elif distro.startswith('centos'):
        return 'centos'
    elif distro.startswith('linuxmint'):
        return 'ubuntu'
    return distro


def _normalized_release(release):
    """
    A normalizer function to make sense of distro
    release versions.

    Returns an object with: major, minor, patch, and garbage

    These attributes can be accessed as ints with prefixed "int"
    attribute names, for example:

        normalized_version.int_major
    """
    # TODO: at some point deprecate this function so that we just
    # use this class directly (and update every test that calls it
    return versions.NormalizedVersion(release)
