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
