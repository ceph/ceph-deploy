import ConfigParser
import logging
import re

from . import conf
from . import exc


log = logging.getLogger(__name__)


def mon(args):
    cfg = conf.load(args)
    if not args.mon:
        try:
            mon_initial_members = cfg.get('global', 'mon_initial_members')
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            pass
        else:
            args.mon = re.split(r'[,\s]+', mon_initial_members)

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
