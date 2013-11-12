import argparse
import logging
from distutils.util import strtobool

from . import hosts
from .cliutil import priority
from .lib.remoto import process


LOG = logging.getLogger(__name__)


def ceph_is_installed(conn):
    """
    Check if the ceph packages are installed by looking for the
    presence of the ceph command.
    """
    stdout, stderr, return_code = process.check(
        conn,
        ['which', 'ceph'],
    )
    return not return_code


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
        distro = hosts.get(hostname, username=args.username)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('installing ceph on %s' % hostname)
        distro.install(distro, args.version_kind, version, args.adjust_repos)
        # Check the ceph version we just installed
        hosts.common.ceph_version(distro.conn)
        distro.conn.exit()


def uninstall(args):
    LOG.debug(
        'Uninstalling on cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        distro = hosts.get(hostname, username=args.username)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('uninstalling ceph on %s' % hostname)
        distro.uninstall(distro.conn)
        distro.conn.exit()


def purge(args):
    LOG.debug(
        'Purging from cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        distro = hosts.get(hostname, username=args.username)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('purging host ... %s' % hostname)
        distro.uninstall(distro.conn, purge=True)
        distro.conn.exit()


def purge_data(args):
    LOG.debug(
        'Purging data from cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    installed_hosts = []
    for hostname in args.host:
        distro = hosts.get(hostname, username=args.username)
        if ceph_is_installed(distro.conn):
            installed_hosts.append(hostname)
        distro.conn.exit()

    if installed_hosts:
        print "ceph is still installed on: ", installed_hosts
        answer = raw_input("Continue (y/n)")
        if not strtobool(answer):
            return

    for hostname in args.host:
        distro = hosts.get(hostname, username=args.username)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('purging data on %s' % hostname)

        process.run(
            distro.conn,
            [
                'rm', '-rf', '--one-file-system', '--', '/var/lib/ceph',
            ]
        )
        if distro.conn.remote_module.path_exists('/var/lib/ceph'):
            process.run(
                distro.conn,
                [
                    'find', '/var/lib/ceph',
                    '-mindepth', '1',
                    '-maxdepth', '2',
                    '-type', 'd',
                    '-exec', 'umount', '{}', ';',
                ]
            )
            process.run(
                distro.conn,
                [
                    'rm', '-rf', '--one-file-system', '--', '/var/lib/ceph',
                ]
            )

        process.run(
            distro.conn,
            [
                'rm', '-rf', '--one-file-system', '--', '/etc/ceph/*',
            ]
        )

        distro.conn.exit()


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

    version.add_argument(
        '--adjust-repos',
        dest='adjust_repos',
        action='store_true',
        help='install packages modifying source repos',
    )

    version.add_argument(
        '--no-adjust-repos',
        dest='adjust_repos',
        action='store_false',
        help='install packages without modifying source repos',
    )

    version.set_defaults(
        func=install,
        stable='emperor',
        dev='master',
        version_kind='stable',
        adjust_repos=True,
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
