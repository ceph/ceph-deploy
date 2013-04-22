import logging
import subprocess

from . import exc
from . import conf
from . import lsb
from .cliutil import priority
from .sudo_pushy import get_transport

LOG = logging.getLogger(__name__)

def update_apt():
    import subprocess

    # must define this inside to be able to use it with pushy
    def gather_stderr(*args, **kwargs):
        p = subprocess.Popen(*args, **kwargs)
        (out, err) = p.communicate()
        rc = p.returncode
        if rc == 0:
            return None
        return ' '.join(args[0]) + ': error code {}\n'.format(rc) + err

    # update apt configuration if file is not present or empty
    APT_CONF_LINE = 'deb http://ceph.com/debian-ceph-deploy precise main'

    with open('/etc/apt/sources.list.d/ceph-deploy.list', 'a+') as f:
        if not len(f.readlines()):
            f.write(APT_CONF_LINE + '\n')
    s = gather_stderr(['/usr/bin/apt-get', '-q', 'update'],
                      stderr=subprocess.PIPE)
    if s:
        return s
    s = gather_stderr(['/usr/bin/apt-get', '-qy', 'install', 'ceph-deploy'],
                      stderr = subprocess.PIPE)
    return s

def update_yum():
    import subprocess

    def gather_stderr(*args, **kwargs):
        p = subprocess.Popen(*args, **kwargs)
        (out, err) = p.communicate()
        rc = p.returncode
        if rc == 0:
            return None
        return ' '.join(args[0]) + ': error code {}\n'.format(rc) + err

    return gather_stderr(['/usr/bin/yum', 'install', 'ceph-deploy'])

def update(args):
    LOG.info("Checking for/installing new ceph-deploy packages")
    sudo = args.pushy("local+sudo:")
    (distro, release, codename) = lsb.get_lsb_release(sudo)
    if distro == 'Debian' or distro == 'Ubuntu':
        sudo_r = sudo.compile(update_apt)
    elif distro == 'CentOS':
        sudo_r = sudo.compile(update_yum)
    else:
        raise exc.UnsupportedPlatform(distro, codename)
    s = sudo_r()
    if s:
        LOG.error("Error installing latest ceph-deploy packages:")
        LOG.error(s)
    else:
        LOG.info("Updated ceph-deploy")


@priority(80)
def make(parser):
    """
    Install latest ceph-deploy packages.
    """
    parser.set_defaults(
        func=update,
        )

