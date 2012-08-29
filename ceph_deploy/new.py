import ConfigParser
import logging
import os


log = logging.getLogger(__name__)


def new(args):
    # TODO validate cluster name in arg parsing
    log.debug('Creating new cluster named %r', args.cluster)
    cfg = ConfigParser.RawConfigParser()
    cfg.add_section('global')
    tmp = '{name}.{pid}.tmp'.format(
        name=args.cluster,
        pid=os.getpid(),
        )
    path = '{name}.conf'.format(
        name=args.cluster,
        )
    try:
        with file(tmp, 'w') as f:
            cfg.write(f)
        os.link(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def make(parser):
    """
    Start deploying a new cluster, and write a CLUSTER.conf for it.
    """
    parser.add_argument(
        'cluster',
        metavar='CLUSTER',
        help='name of the new cluster',
        )
    parser.add_argument(
        'mon',
        metavar='MON',
        nargs='*',
        help='initial monitor hosts',
        )
    parser.set_defaults(
        func=new,
        )
