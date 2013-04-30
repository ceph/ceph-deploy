import logging
import subprocess

from . import exc
from . import conf
from . import lsb
from .cliutil import priority
from .sudo_pushy import get_transport

APT_SOURCES_LIST_LINE = 'deb http://ceph.com/packages/ceph-deploy/debian precise main'
APT_KEY_LOC = 'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/autobuild.asc'
YUM_REPO_UPDATE = ''
YUM_KEY_LOC = ''

LOG = logging.getLogger(__name__)

def update_apt(sources_list_line, key_loc):
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

    with open('/etc/apt/sources.list.d/ceph-deploy.list', 'a+') as f:
        if not len(f.readlines()):
            f.write(sources_list_line + '\n')

    s = gather_stderr(
        args='wget -q -O- \'{}\' | apt-key add -'.format(key_loc),
        shell=True
        )
    if s:
        return s

    s = gather_stderr(['/usr/bin/apt-get', '-q', 'update'],
                      stderr=subprocess.PIPE)
    if s:
        return s

    return gather_stderr(['/usr/bin/apt-get', '-qy', 'install', 'ceph-deploy'],
                      stderr = subprocess.PIPE)

def update_yum(rpm_url, key_url):
    import subprocess

    def gather_stderr(*args, **kwargs):
        p = subprocess.Popen(*args, **kwargs)
        (out, err) = p.communicate()
        rc = p.returncode
        if rc == 0:
            return None
        return ' '.join(args[0]) + ': error code {}\n'.format(rc) + err

    s = gather_stderr(['/usr/bin/rpm', '--import', key_url])
    if s:
        return s

    s = gather_stderr(['/usr/bin/rpm', '-Uvh', '--quiet', rpm_url])
    if s:
        return s

    return gather_stderr(['/usr/bin/yum', '-yq', 'install', 'ceph-deploy'])

def update(args):
    LOG.info("Checking for/installing new ceph-deploy packages")

    sudo = args.pushy("local+sudo:")
    (distro, release, codename) = lsb.get_lsb_release(sudo)
    if distro == 'Debian' or distro == 'Ubuntu':
        sudo_r = sudo.compile(update_apt)
        s = sudo_r(APT_SOURCES_LIST_LINE, APT_KEY_LOC)
    elif distro == 'CentOS':
        sudo_r = sudo.compile(update_yum)
        s = sudo_r(YUM_REPO_UPDATE, YUM_KEY_LOC)
    else:
        raise exc.UnsupportedPlatform(distro, codename)
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

