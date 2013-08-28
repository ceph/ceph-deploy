import os.path
import logging

from .cliutil import priority
from . import misc
from .sudo_pushy import get_transport

LOG = logging.getLogger(__name__)

def fetch_file(args, frompath, topath, hosts):
    # mon.
    if os.path.exists(topath):
        LOG.debug('Have %s', topath)
        return True
    else:
        for hostname in hosts:
            LOG.debug('Checking %s for %s', hostname, frompath)
            sudo = args.pushy(get_transport(hostname))
            get_file_r = sudo.compile(misc.get_file)
            key = get_file_r(path=frompath.format(hostname=hostname))
            if key is not None:
                LOG.debug('Got %s key from %s.', topath, hostname)
                with file(topath, 'w') as f:
                    f.write(key)
                    return True
            sudo.close()
    LOG.warning('Unable to find %s on %s', frompath, hosts)
    return False

def gatherkeys(args):
    ret = 0

    # client.admin
    r = fetch_file(
        args=args,
        frompath='/etc/ceph/{cluster}.client.admin.keyring'.format(
            cluster=args.cluster),
        topath='{cluster}.client.admin.keyring'.format(
            cluster=args.cluster),
        hosts=args.mon,
        )
    if not r:
        ret = 1

    # mon.
    r = fetch_file(
        args=args,
        frompath='/var/lib/ceph/mon/%s-{hostname}/keyring' % args.cluster,
        topath='{cluster}.mon.keyring'.format(
             cluster=args.cluster),
        hosts=args.mon,
        )
    if not r:
        ret = 1

    # bootstrap
    for what in ['osd', 'mds']:
        r = fetch_file(
            args=args,
            frompath='/var/lib/ceph/bootstrap-{what}/{cluster}.keyring'.format(
                cluster=args.cluster,
                what=what),
            topath='{cluster}.bootstrap-{what}.keyring'.format(
                cluster=args.cluster,
                what=what),
            hosts=args.mon,
            )
        if not r:
            ret = 1

    return ret

@priority(40)
def make(parser):
    """
    Gather authentication keys for provisioning new nodes.
    """
    parser.add_argument(
        'mon',
        metavar='HOST',
        nargs='+',
        help='monitor host to pull keys from',
        )
    parser.set_defaults(
        func=gatherkeys,
        )
