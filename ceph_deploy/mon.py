import ConfigParser
import logging

from . import conf
from . import exc


log = logging.getLogger(__name__)


def mon(args):
    cfg = conf.load(args)
    if not args.mon:
        try:
            args.mon = cfg.get('global', 'mon_initial_members')
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            pass

    if not args.mon:
        raise exc.NeedHostError()

    log.debug(
        'Deploying mon, cluster %s hosts %s',
        args.cluster,
        ' '.join(args.mon),
        )
    raise NotImplementedError('TODO')


def make(parser):
    """
    Deploy ceph monitor on remote hosts.
    """
    parser.add_argument(
        'mon',
        metavar='MON',
        nargs='*',
        help='host to deploy on',
        )
    parser.set_defaults(
        func=mon,
        )
