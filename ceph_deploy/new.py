import ConfigParser
import errno
import logging
import os
import uuid

from . import exc
from .cliutil import priority


log = logging.getLogger(__name__)


def new(args):
    log.debug('Creating new cluster named %s', args.cluster)
    cfg = ConfigParser.RawConfigParser()
    cfg.add_section('global')

    fsid = uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))

    if args.mon:
        cfg.set('global', 'mon_initial_members', ', '.join(args.mon))
        # no spaces here, see http://tracker.newdream.net/issues/3145
        cfg.set('global', 'mon_host', ','.join(args.mon))

    # override undesirable defaults, needed until bobtail

    # http://tracker.newdream.net/issues/3136
    cfg.set('global', 'auth supported', 'cephx')

    # http://tracker.newdream.net/issues/3137
    cfg.set('global', 'osd_journal_size', '1024')

    # http://tracker.newdream.net/issues/3138
    cfg.set('global', 'filestore_xattr_use_omap', 'true')

    tmp = '{name}.{pid}.tmp'.format(
        name=args.cluster,
        pid=os.getpid(),
        )
    path = '{name}.conf'.format(
        name=args.cluster,
        )

    # FIXME: create a random key
    monkey = '[mon.]\n   key = AQBWDj5QAP6LHhAAskVBnUkYHJ7eYREmKo5qKA=='

    keypath = '{name}.mon.keyring'.format(
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

        with file(tmp, 'w') as f:
            f.write(mon_keyring)
        try:
            os.link(tmp, keypath)
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


@priority(10)
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
