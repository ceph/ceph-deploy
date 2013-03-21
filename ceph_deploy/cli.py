import pkg_resources
import argparse
import logging
import pushy
import sys

from . import exc
from . import validate
from . import sudo_pushy


LOG = logging.getLogger(__name__)


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(
        description='Deploy Ceph',
        )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true', dest='verbose', default=True,
        help='be more verbose',
        )
    parser.add_argument(
        '-q', '--quiet',
        action='store_false', dest='verbose',
        help='be less verbose',
        )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true', dest='dry_run',
        help='do not perform any action, but report what would be done',
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
    args = parser.parse_args(args=args, namespace=namespace)
    return args


def main(args=None, namespace=None):
    args = parse_args(args=args, namespace=namespace)

    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG

    logging.basicConfig(
        level=loglevel,
        )

    sudo_pushy.patch()

    try:
        return args.func(args)
    except exc.DeployError as e:
        print >> sys.stderr, '{prog}: {msg}'.format(
            prog=args.prog,
            msg=e,
            )
        sys.exit(1)
