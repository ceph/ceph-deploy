import argparse
import logging
import pkg_resources
import pushy
import sys

from . import exc
from . import validate
from . import sudo_pushy


log = logging.getLogger(__name__)


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(
        description='Deploy Ceph',
        )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true', default=None,
        help='be more verbose',
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
    for ep in pkg_resources.iter_entry_points('ceph_deploy.cli'):
        fn = ep.load()
        p = sub.add_parser(
            ep.name,
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
        print >>sys.stderr, '{prog}: {msg}'.format(
            prog=args.prog,
            msg=e,
            )
        sys.exit(1)
