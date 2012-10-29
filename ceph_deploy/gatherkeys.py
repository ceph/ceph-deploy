import argparse
import logging
import os.path

from cStringIO import StringIO

from . import exc
from .cliutil import priority


log = logging.getLogger(__name__)


def get_file(path):
     """
     Run on mon node, grab a file.
     """
     try:
         with file(path, 'rb') as f:
             return f.read()
     except IOError:
         pass

def fetch_file(args, frompath, topath, hosts):
    # mon.
    if os.path.exists(topath):
        log.debug('Have %s', topath)
    else:
        for hostname in hosts:
            log.debug('Checking %s for %s', hostname, frompath)
            sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
            get_file_r = sudo.compile(get_file)
            key = get_file_r(path=frompath.format(hostname=hostname))
            if key is not None:
                log.debug('Got %s key from %s.', topath, hostname)
                with file(topath, 'w') as f:
                    f.write(key)
                    return True
    return False

def gatherkeys(args):
    # client.admin
    fetch_file(
        args=args,
        frompath='/etc/ceph/{cluster}.client.admin.keyring'.format(
            cluster=args.cluster),
        topath='{cluster}.client.admin.keyring'.format(
            cluster=args.cluster),
        hosts=args.mon,
        )

    # mon.
    fetch_file(
        args=args,
        frompath='/var/lib/ceph/mon/%s-{hostname}/keyring' % args.cluster,
        topath='{cluster}.mon.keyring'.format(
            cluster=args.cluster),
        hosts=args.mon,
        )

    # bootstrap
    for what in ['osd']:
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
        if r:
            break


@priority(40)
def make(parser):
    """
    Gather authentication keys for provisioning new nodes.
    """
    parser.add_argument(
        'mon',
        metavar='HOST',
        nargs='*',
        help='monitor host to pull keys from',
        )
    parser.set_defaults(
        func=gatherkeys,
        )
