import argparse
import logging
from distutils.util import strtobool
import os

from . import hosts
from .cliutil import priority
from .lib.remoto import process
from .lib.remoto.connection import needs_ssh
from .connection import get_connection


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
        ssh_copy_keys(hostname)
        LOG.debug('Detecting platform for host %s ...', hostname)
        distro = hosts.get(hostname, username=args.username)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('installing ceph on %s' % hostname)
        distro.install(distro, args.version_kind, version, args.adjust_repos)
        # Check the ceph version we just installed
        hosts.common.ceph_version(distro.conn)
        distro.conn.exit()


def ssh_copy_keys(hostname):
    # Ensure we are not doing this for local hosts
    if not needs_ssh(hostname):
        return
    LOG.info('making sure passwordless SSH succeeds')
    logger = logging.getLogger(hostname)
    local_conn = get_connection(
        'localhost',
        None,
        logger,
        threads=1,
        use_sudo=False
    )

    # Check to see if we can login, disabling password prompts
    command = ['ssh', '-CT', '-o', 'BatchMode=yes', hostname]
    out, err, retval = process.check(local_conn, command, stop_on_error=False)
    expected_error = 'Permission denied (publickey,password)'
    expected_retval = 255
    has_key_error = False
    for line in err:
        if expected_error in line:
            has_key_error = True

    if retval == expected_retval and has_key_error:
        LOG.warning('could not connect via SSH')
        LOG.info('will connect again with password prompt')
        # Create the key if it doesn't exist:
        if not os.path.exists(os.path.expanduser(u'~/.ssh/id_rsa.pub')):
            LOG.info('creating a passwordless id_rsa.pub key file')
            process.run(local_conn, ['ssh-keygen', '-t', 'rsa', '-N', "''"])
        else:  # Get the contents of id_rsa.pub and push it to the host
            distro = hosts.get(hostname)  # XXX Add username
            auth_keys_path = '.ssh/authorized_keys'
            if not distro.conn.remote_module.path_exists(auth_keys_path):
                logger.warning('.ssh/authorized_keys does not exist, will skip adding keys')
                local_conn.exit()
                distro.conn.exit()
                return
            else:
                logger.info('adding public keys to authorized_keys')
                with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as id_rsa:
                    contents = id_rsa.read()
                distro.conn.remote_module.append_to_file(
                    auth_keys_path,
                    contents
                )
                distro.conn.exit()
    local_conn.exit()


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
        stable='dumpling',
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
