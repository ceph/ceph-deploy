import pkg_resources
import argparse
import logging
import pushy
import textwrap
import sys

import ceph_deploy
from . import exc
from . import validate
from . import sudo_pushy
from pushy.client import ClientInitException
from .util import log
from .util.decorators import catches

LOG = logging.getLogger(__name__)


__header__ = textwrap.dedent("""
    -^-
   /   \\
   |O o|  ceph-deploy v%s
   ).-.(
  '/|||\`
  | '|` |
    '|`
""" % ceph_deploy.__version__)


def get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Easy Ceph deployment\n\n%s' % __header__,
        )
    verbosity = parser.add_mutually_exclusive_group(required=False)
    verbosity.add_argument(
        '-v', '--verbose',
        action='store_true', dest='verbose', default=False,
        help='be more verbose',
        )
    verbosity.add_argument(
        '-q', '--quiet',
        action='store_true', dest='quiet',
        help='be less verbose',
        )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true', dest='dry_run',
        help='do not perform any action, but report what would be done',
        )
    parser.add_argument(
        '--version',
        action='version',
        version='%s' % ceph_deploy.__version__,
        help='the current installed version of ceph-deploy',
        )
    parser.add_argument(
        '--overwrite-conf',
        action='store_true',
        help='overwrite an existing conf file on remote host (if present)',
        )
    parser.add_argument(
        '--cluster',
        metavar='NAME',
        help='name of the cluster',
        type=validate.alphanumeric,
        )
    sub = parser.add_subparsers(
        title='commands',
        metavar='COMMAND',
        help='description',
        )
    entry_points = [
        (ep.name, ep.load())
        for ep in pkg_resources.iter_entry_points('ceph_deploy.cli')
        ]
    entry_points.sort(
        key=lambda (name, fn): getattr(fn, 'priority', 100),
        )
    for (name, fn) in entry_points:
        p = sub.add_parser(
            name,
            description=fn.__doc__,
            help=fn.__doc__,
            )
        # ugly kludge but i really want to have a nice way to access
        # the program name, with subcommand, later
        p.set_defaults(prog=p.prog)
        fn(p)
    parser.set_defaults(
        # we want to hold on to this, for later
        prog=parser.prog,

        # unit tests can override this to mock pushy; no user-visible
        # option sets this
        pushy=pushy.connect,

        cluster='ceph',
        )
    return parser


# TODO: Move the ClientInitException to hosts.get once all actions are using
# hosts.get() to start the remote connection
@catches((
    KeyboardInterrupt,
    RuntimeError,
    exc.DeployError,
    ClientInitException))
def main(args=None, namespace=None):
    parser = get_parser()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args(args=args, namespace=namespace)

    console_loglevel = logging.DEBUG  # start at DEBUG for now
    if args.quiet:
        console_loglevel = logging.WARNING
    if args.verbose:
        console_loglevel = logging.DEBUG

    # Console Logger
    sh = logging.StreamHandler()
    sh.setFormatter(log.color_format())
    sh.setLevel(console_loglevel)

    # File Logger
    fh = logging.FileHandler('{cluster}.log'.format(cluster=args.cluster))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(log.BASE_FORMAT))

    # because we're in a module already, __name__ is not the ancestor of
    # the rest of the package; use the root as the logger for everyone
    root_logger = logging.getLogger()

    # allow all levels at root_logger, handlers control individual levels
    root_logger.setLevel(logging.DEBUG)

    root_logger.addHandler(sh)
    root_logger.addHandler(fh)

    sudo_pushy.patch()

    return args.func(args)
