import argparse
import logging

from . import exc
from . import lsb
from .cliutil import priority

LOG = logging.getLogger(__name__)

def install_centos(release, codename, version_kind, version):
    import platform
    import subprocess

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    subprocess.check_call(
        args='su -c \'rpm --import "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc"\''.format(key=key),
        shell=True,
        )

    if version_kind == 'stable':
        url = 'http://ceph.com/rpm-{version}/'.format(
        version=version,
        )
    elif version_kind == 'testing':
        url = 'http://ceph.com/rpm-testing/'
    elif version_kind == 'dev':
        url = 'http://gitbuilder.ceph.com/ceph-rpm-centos{release}-{machine}-basic/ref/{version}/'.format(
            release=release.split(".",1)[0],
            machine=platform.machine(),
            version=version,
            )

    subprocess.call(
        args=['rpm', '-Uvh','--quiet', '{url}noarch/ceph-release-1-0.el6.noarch.rpm'.format(
            url=url
            )]
        )
    
    subprocess.check_call(
        args=[
            'yum',
            '-y',
            '-q',
            'install',
            'ceph',
            'ceph-common',
            'ceph-fs-common',
            ],
        )
    
def uninstall_centos():
    import subprocess

    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
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

def install_debian(release, codename, version_kind, version):
    import platform
    import subprocess

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    subprocess.check_call(
        args='wget -q -O- \'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc\' | apt-key add -'.format(key=key),
        shell=True,
        )

    if version_kind == 'stable':
        url = 'http://ceph.com/debian-{version}/'.format(
            version=version,
            )
    elif version_kind == 'testing':
        url = 'http://ceph.com/debian-testing/'
    elif version_kind == 'dev':
        url = 'http://gitbuilder.ceph.com/ceph-deb-{codename}-{machine}-basic/ref/{version}'.format(
            codename=codename,
            machine=platform.machine(),
            version=version,
            )
    else:
        raise RuntimeError('Unknown version kind: %r' % version_kind)

    with file('/etc/apt/sources.list.d/ceph.list', 'w') as f:
        f.write('deb {url} {codename} main\n'.format(
                url=url,
                codename=codename,
                ))

    subprocess.check_call(
        args=[
            'apt-get',
            '-q',
            'update',
            ],
        )

    # TODO this does not downgrade -- should it?
    subprocess.check_call(
        args=[
            'env',
            'DEBIAN_FRONTEND=noninteractive',
            'DEBIAN_PRIORITY=critical',
            'apt-get',
            '-q',
            '-o', 'Dpkg::Options::=--force-confnew',
            'install',
            '--no-install-recommends',
            '--assume-yes',
            '--',
            'ceph',
            'ceph-mds',
            'ceph-common',
            'ceph-fs-common',
            # ceph only recommends gdisk, make sure we actually have
            # it; only really needed for osds, but minimal collateral
            'gdisk',
            ],
        )

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
        LOG.debug('Detecting platform for host %s ...', hostname)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
        lsb_release_r = sudo.compile(lsb.lsb_release)
        (distro, release, codename) = lsb_release_r()
        LOG.debug('Distro %s release %s codename %s', distro, release, codename)

        if (distro == 'Debian' or distro == 'Ubuntu'):
            LOG.debug('Installing on host %s ...', hostname)
            install_r = sudo.compile(install_debian)
        elif (distro == 'CentOS'):
            LOG.debug('Installing on host %s ...', hostname)
            install_r = sudo.compile(install_centos)
        else:
            raise exc.UnsupportedPlatform(distro=distro, codename=codename)

        install_r(
            release=release,
            codename=codename,
            version_kind=args.version_kind,
            version=version,
            )

def uninstall(args):
    LOG.debug(
        'Uninstalling on cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
        lsb_release_r = sudo.compile(lsb.lsb_release)
        (distro, release, codename) = lsb_release_r()
        LOG.debug('Distro %s codename %s', distro, codename)

        if (distro == 'Debian' or distro == 'Ubuntu'):
            LOG.debug('Uninstalling on host %s ...', hostname)
            uninstall_r = sudo.compile(uninstall_debian)
        elif (distro == 'centos'):
            LOG.debug('Uninstalling on host %s ...', hostname)
            uninstall_r = sudo.compile(uninstall_centos)
        else:
            raise exc.UnsupportedPlatform(distro=distro, codename=codename)

        uninstall_r()

def purge(args):
    LOG.debug(
        'Purging from cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
        lsb_release_r = sudo.compile(lsb.lsb_release)
        (distro, release, codename) = lsb_release_r()
        LOG.debug('Distro %s codename %s', distro, codename)

        if (distro == 'Debian' or distro == 'Ubuntu'):
            LOG.debug('Purging host %s ...', hostname)
            purge_r = sudo.compile(uninstall_debian)
        else:
            raise exc.UnsupportedPlatform(distro=distro, codename=codename)

        purge_r(purge=True)

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
            'argonaut',
            'bobtail',
            'cuttlefish',
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
        stable='bobtail',
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
