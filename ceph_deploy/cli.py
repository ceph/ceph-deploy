import argparse
import logging
import pkg_resources
import sys

from . import exc


log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Deploy Ceph',
        )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true', default=None,
        help='be more verbose',
        )
    sub = parser.add_subparsers(
        title='commands',
        metavar='COMMAND',
        help='description',
        )
    for ep in pkg_resources.iter_entry_points('ceph_deploy.cli'):
        fn = ep.load()
        p = sub.add_parser(ep.name, help=fn.__doc__)
        # ugly kludge but i really want to have a nice way to access
        # the program name, with subcommand, later
        p.set_defaults(prog=p.prog)
        fn(p)
    parser.set_defaults(
        # we want to hold on to this, for later
        prog=parser.prog,
        )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG

    logging.basicConfig(
        level=loglevel,
        )

    try:
        return args.func(args)
    except exc.DeployError as e:
        print >>sys.stderr, '{prog}: {msg}'.format(
            prog=args.prog,
            msg=e,
            )
        sys.exit(1)
