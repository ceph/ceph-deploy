import pkg_resources
import argparse
import logging
import textwrap
import os
import sys

import ceph_deploy
from ceph_deploy import exc, validate
from ceph_deploy.util import log
from ceph_deploy.util.decorators import catches

LOG = logging.getLogger(__name__)


__header__ = textwrap.dedent("""
    -^-
   /   \\
   |O o|  ceph-deploy v%s
   ).-.(
  '/|||\`
  | '|` |
    '|`

Full documentation can be found at: http://ceph.com/ceph-deploy/docs
""" % ceph_deploy.__version__)


def log_flags(args, logger=None):
    logger = logger or LOG
    logger.info('ceph-deploy options:')

    for k, v in args.__dict__.items():
        if k.startswith('_'):
            continue
        logger.info(' %-30s: %s' % (k, v))


def get_parser():
    parser = argparse.ArgumentParser(
        prog='ceph-deploy',
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
        '--version',
        action='version',
        version='%s' % ceph_deploy.__version__,
        help='the current installed version of ceph-deploy',
        )
    parser.add_argument(
        '--username',
        help='the username to connect to the remote host',
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
    parser.add_argument(
        '--ceph-conf',
        dest='ceph_conf',
        help='use (or reuse) a given ceph.conf file',
    )
    sub = parser.add_subparsers(
        title='commands',
        metavar='COMMAND',
        help='description',
        )
    sub.required = True
    entry_points = [
        (ep.name, ep.load())
        for ep in pkg_resources.iter_entry_points('ceph_deploy.cli')
        ]
    entry_points.sort(
        key=lambda name_fn: getattr(name_fn[1], 'priority', 100),
        )
    for (name, fn) in entry_points:
        p = sub.add_parser(
            name,
            description=fn.__doc__,
            help=fn.__doc__,
            )
        if not os.environ.get('CEPH_DEPLOY_TEST'):
            p.set_defaults(cd_conf=ceph_deploy.conf.cephdeploy.load())

        # flag if the default release is being used
        p.set_defaults(default_release=False)
        fn(p)
        p.required = True
    parser.set_defaults(
        cluster='ceph',
        )

    return parser


@catches((KeyboardInterrupt, RuntimeError, exc.DeployError,), handle_all=True)
def _main(args=None, namespace=None):
    # Set console logging first with some defaults, to prevent having exceptions
    # before hitting logging configuration. The defaults can/will get overridden
    # later.

    # Console Logger
    sh = logging.StreamHandler()
    sh.setFormatter(log.color_format())
    sh.setLevel(logging.WARNING)

    # because we're in a module already, __name__ is not the ancestor of
    # the rest of the package; use the root as the logger for everyone
    root_logger = logging.getLogger()

    # allow all levels at root_logger, handlers control individual levels
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(sh)

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
    sh.setLevel(console_loglevel)

    # File Logger
    fh = logging.FileHandler('ceph-deploy-{cluster}.log'.format(cluster=args.cluster))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(log.FILE_FORMAT))

    root_logger.addHandler(fh)

    # Reads from the config file and sets values for the global
    # flags and the given sub-command
    # the one flag that will never work regardless of the config settings is
    # logging because we cannot set it before hand since the logging config is
    # not ready yet. This is the earliest we can do.
    args = ceph_deploy.conf.cephdeploy.set_overrides(args)

    LOG.info("Invoked (%s): %s" % (
        ceph_deploy.__version__,
        ' '.join(sys.argv))
    )
    log_flags(args)

    return args.func(args)


def main(args=None, namespace=None):
    try:
        _main(args=args, namespace=namespace)
    finally:
        # This block is crucial to avoid having issues with
        # Python spitting non-sense thread exceptions. We have already
        # handled what we could, so close stderr and stdout.
        if not os.environ.get('CEPH_DEPLOY_TEST'):
            try:
                sys.stdout.close()
            except:
                pass
            try:
                sys.stderr.close()
            except:
                pass
