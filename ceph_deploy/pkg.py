import logging
from . import hosts


LOG = logging.getLogger(__name__)


def install(args):
    packages = args.install.split(',')
    for hostname in args.hosts:
        distro = hosts.get(hostname, username=args.username)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )
        rlogger = logging.getLogger(hostname)
        rlogger.info('installing packages on %s' % hostname)
        # Do not timeout on package install. If you we this command to install
        # e.g. ceph-selinux or some other package with long post script we can
        # easily timeout in the 5 minutes that we use as a default timeout,
        # turning off the timeout completely for the time we run the command
        # should make this much more safe.
        distro.conn.global_timeout = None
        distro.packager.install(packages)
        distro.conn.exit()


def remove(args):
    packages = args.remove.split(',')
    for hostname in args.hosts:
        distro = hosts.get(hostname, username=args.username)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        rlogger = logging.getLogger(hostname)
        rlogger.info('removing packages from %s' % hostname)
        # Do not timeout on package removal. If we use this command to remove
        # e.g. ceph-selinux or some other package with long post script we can
        # easily timeout in the 5 minutes that we use as a default timeout,
        # turning off the timeout completely for the time we run the command
        # should make this much more safe.
        distro.conn.global_timeout = None
        distro.packager.remove(packages)
        distro.conn.exit()


def pkg(args):
    if args.install:
        install(args)
    elif args.remove:
        remove(args)


def make(parser):
    """
    Manage packages on remote hosts.
    """

    action = parser.add_mutually_exclusive_group()

    action.add_argument(
        '--install',
        metavar='PKG(s)',
        help='Comma-separated package(s) to install',
    )

    action.add_argument(
        '--remove',
        metavar='PKG(s)',
        help='Comma-separated package(s) to remove',
    )

    parser.add_argument(
        'hosts',
        nargs='+',
    )

    parser.set_defaults(
        func=pkg,
    )
