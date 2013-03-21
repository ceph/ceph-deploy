import logging
import os.path

from .cliutil import priority


LOG = logging.getLogger(__name__)


def get_file(path):
    """
    Run on remote node, grab a file.
    """
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        pass

def fetch_file(args, frompath, topath, hosts):
    # mon.
    if os.path.exists(topath):
        LOG.debug('Have %s', topath)
        return True
    else:
        for hostname in hosts:
            LOG.debug('Checking %s for %s', hostname, frompath)
            sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
            get_file_r = sudo.compile(get_file)
            key = get_file_r(path=frompath.format(hostname=hostname))
            if key is not None:
                LOG.debug('Got %s from %s, writing locally', topath, hostname)
                if not args.dry_run:
                    with file(topath, 'w') as f:
                        f.write(key)
                return True
    LOG.warning('Unable to find %s on %s', frompath, hosts)
    return False

def discover(args):
    ret = 0

    # ceph.conf
    r = fetch_file(
        args=args,
        frompath='/etc/ceph/{cluster}.conf'.format(cluster=args.cluster),
        topath='{cluster}.conf'.format(cluster=args.cluster),
        hosts=args.host,
        )
    if not r:
        ret = 1

    return ret

@priority(10)
def make(parser):
    """
    Gather cluster configuration from another host to CLUSTER.conf.
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='*',
        help='host to pull cluster information from',
        )
    parser.set_defaults(
        func=discover,
        )
