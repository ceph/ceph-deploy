import ConfigParser
import errno
import logging
import os
import uuid

from . import exc


log = logging.getLogger(__name__)


def new(args):
    log.debug('Creating new cluster named %r', args.cluster)
    cfg = ConfigParser.RawConfigParser()
    cfg.add_section('global')

    fsid = uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))

    if args.mon:
        cfg.set('global', 'mon_initial_members', ', '.join(args.mon))

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
        try:
            os.link(tmp, path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise exc.ClusterExistsError(path)
            else:
                raise
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
        'mon',
        metavar='MON',
        nargs='*',
        help='initial monitor hosts',
        )
    parser.set_defaults(
        func=new,
        )
