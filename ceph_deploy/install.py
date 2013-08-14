import argparse
import logging
from distutils.util import strtobool

from . import exc
from . import lsb, hosts
from .cliutil import priority
from .sudo_pushy import get_transport
from .util.decorators import remote_compile

LOG = logging.getLogger(__name__)

def check_ceph_installed():
    """
    Check if the ceph packages are installed by looking for the
    presence of the ceph command.
    """
    import subprocess

    args = [ 'which', 'ceph', ]
    process = subprocess.Popen(
        args=args,
        )
    lsb_release_path, _ = process.communicate()
    return process.wait()


def uninstall_suse(arg_purge=False):
    import subprocess

    packages = [
        'ceph',
        'libcephfs1',
        'librados2',
        'librbd1',
        ]
    args = [
        'zypper',
        '--non-interactive',
        '--quiet',
        'remove',
        ]

    args.extend(packages)
    subprocess.check_call(args=args)

def uninstall_debian(arg_purge=False):
    import subprocess

    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        ]
    args = [
        'apt-get',
        '-q',
        'remove',
        '-f',
        '-y',
        '--force-yes',
        ]
    if arg_purge:
        args.append('--purge')
    args.append('--')
    args.extend(packages)
    subprocess.check_call(args=args)


def uninstall_fedora(arg_purge=False):
    import subprocess

    packages = [
        'ceph',
        ]
    args = [
        'yum',
        '-q',
        '-y',
        'remove',
        ]

    args.extend(packages)
    subprocess.check_call(args=args)


def uninstall_centos(arg_purge=False):
    import subprocess

    packages = [
        'ceph',
        ]
    args = [
        'yum',
        '-q',
        '-y',
        'remove',
        ]

    args.extend(packages)
    subprocess.check_call(args=args)

def uninstall_debian(arg_purge=False):
    import subprocess

    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        ]
    args = [
        'apt-get',
        '-q',
        'remove',
        '-f',
        '-y',
        '--force-yes',
        ]
    if arg_purge:
        args.append('--purge')
    args.append('--')
    args.extend(packages)
    subprocess.check_call(args=args)


def purge_data_any():
    import subprocess
    import os.path

    subprocess.call(args=[
            'rm', '-rf', '--one-file-system', '--', '/var/lib/ceph',
            ])
    if os.path.exists('/var/lib/ceph'):
        subprocess.check_call(args=[
                'find', '/var/lib/ceph',
                '-mindepth', '1',
                '-maxdepth', '2',
                '-type', 'd',
                '-exec', 'umount', '{}', ';',
                ])
        subprocess.check_call(args=[
                'rm', '-rf', '--one-file-system', '--', '/var/lib/ceph',
                ])
    subprocess.check_call(args=[
            'rm', '-rf', '--one-file-system', '--', '/etc/ceph',
            ])


def install(args):
    version = getattr(args, args.version_kind)
    version_str = args.version_kind
    if version:
        version_str += ' version {version}'.format(version=version)
    LOG.debug(
        'Installing %s on cluster %s hosts %s',
        version_str,
        args.cluster,
        ' '.join(args.host),
        )
    for hostname in args.host:
        # TODO username
        LOG.debug('Detecting platform for host %s ...', hostname)
        distro = hosts.get(hostname)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('installing ceph on %s' % hostname)
        distro.install(distro, rlogger, args.version_kind, version)
        distro.sudo_conn.close()


def uninstall(args):
    LOG.debug(
        'Uninstalling on cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        # TODO username
        sudo = args.pushy(get_transport(hostname))
        (distro, release, codename) = lsb.get_lsb_release(sudo)
        LOG.debug('Distro %s codename %s', distro, codename)

        if (distro == 'Debian' or distro == 'Ubuntu'):
            uninstall_r = sudo.compile(uninstall_debian)
        elif distro == 'CentOS' or distro == 'Scientific' or distro.startswith('RedHat'):
            uninstall_r = sudo.compile(uninstall_centos)
        elif distro == 'Fedora':
            uninstall_r = sudo.compile(uninstall_fedora)
        elif (distro == 'SUSE LINUX'):
            uninstall_r = sudo.compile(uninstall_suse)
        else:
            raise exc.UnsupportedPlatform(distro=distro, codename=codename)

        LOG.debug('Uninstalling on host %s ...', hostname)
        uninstall_r()
        sudo.close()

def purge(args):
    LOG.debug(
        'Purging from cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        # TODO username
        sudo = args.pushy(get_transport(hostname))
        (distro, release, codename) = lsb.get_lsb_release(sudo)
        LOG.debug('Distro %s codename %s', distro, codename)

        if distro == 'Debian' or distro == 'Ubuntu':
            purge_r = sudo.compile(uninstall_debian)
        elif distro == 'CentOS' or distro == 'Scientific' or distro.startswith('RedHat'):
            purge_r = sudo.compile(uninstall_centos)
        elif distro == 'Fedora':
            purge_r = sudo.compile(uninstall_fedora)
        elif (distro == 'SUSE LINUX'):
            purge_r = sudo.compile(uninstall_suse)
        else:
            raise exc.UnsupportedPlatform(distro=distro, codename=codename)

        LOG.debug('Purging host %s ...', hostname)
        purge_r(arg_purge=True)
        sudo.close()

def purge_data(args):
    LOG.debug(
        'Purging data from cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    installed_hosts=[]
    for hostname in args.host:
        sudo = args.pushy(get_transport(hostname))
        check_ceph_installed_r  = sudo.compile(check_ceph_installed)
        status = check_ceph_installed_r()
        if status == 0:
            installed_hosts.append(hostname)
        sudo.close()

    if installed_hosts:
        print "ceph is still installed on: ", installed_hosts
        answer=raw_input("Continue (y/n)")
        if not strtobool(answer):
            return

    for hostname in args.host:
        # TODO username
        sudo = args.pushy(get_transport(hostname))

        LOG.debug('Purging data from host %s ...', hostname)
        purge_data_any_r = sudo.compile(purge_data_any)
        purge_data_any_r()
        sudo.close()

class StoreVersion(argparse.Action):
    """
    Like ``"store"`` but also remember which one of the exclusive
    options was set.

    There are three kinds of versions: stable, testing and dev.
    This sets ``version_kind`` to be the right one of the above.

    This kludge essentially lets us differentiate explicitly set
    values from defaults.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        namespace.version_kind = self.dest


@priority(20)
def make(parser):
    """
    Install Ceph packages on remote hosts.
    """

    version = parser.add_mutually_exclusive_group()

    version.add_argument(
        '--stable',
        nargs='?',
        action=StoreVersion,
        choices=[
            'bobtail',
            'cuttlefish',
            'dumpling',
            'emperor',
            ],
        metavar='CODENAME',
        help='install a release known as CODENAME (done by default) (default: %(default)s)',
        )

    version.add_argument(
        '--testing',
        nargs=0,
        action=StoreVersion,
        help='install the latest development release',
        )

    version.add_argument(
        '--dev',
        nargs='?',
        action=StoreVersion,
        const='master',
        metavar='BRANCH_OR_TAG',
        help='install a bleeding edge build from Git branch or tag (default: %(default)s)',
        )

    version.set_defaults(
        func=install,
        stable='dumpling',
        dev='master',
        version_kind='stable',
        )

    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to install on',
        )
    parser.set_defaults(
        func=install,
        )



@priority(80)
def make_uninstall(parser):
    """
    Remove Ceph packages from remote hosts.
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to uninstall Ceph from',
        )
    parser.set_defaults(
        func=uninstall,
        )

@priority(80)
def make_purge(parser):
    """
    Remove Ceph packages from remote hosts and purge all data.
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to purge Ceph from',
        )
    parser.set_defaults(
        func=purge,
        )


@priority(80)
def make_purge_data(parser):
    """
    Purge (delete, destroy, discard, shred) any Ceph data from /var/lib/ceph
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to purge Ceph data from',
        )
    parser.set_defaults(
        func=purge_data,
        )
