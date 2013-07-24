"""
We deal (mostly) with remote hosts. To avoid special casing each different
commands (e.g. using `yum` as opposed to `apt`) we can make a one time call to
that remote host and set all the special cases for running commands depending
on the type of distribution/version we are dealing with.
"""
import pushy
from ceph_deploy import lsb, exc
from ceph_deploy.sudo_pushy import get_transport
from ceph_deploy.hosts import debian, centos, fedora, suse


def get(hostname):
    sudo_conn = pushy.connect(get_transport(hostname))
    (distro, release, codename) = lsb.get_lsb_release(sudo_conn)

    module = _get_distro(distro)
    module.name = _normalized_distro_name(distro)
    module.release = release
    module.codename = codename
    return module


def _get_distro(distro):
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
        raise exc.UnsupportedPlatform(distro=distro)


def _normalized_distro_name(distro):
    distro = distro.lower()
    if distro.startswith('redhat'):
        return 'redhat'
    elif distro.startswith('suse'):
        return 'suse'
    return distro
