import os.path
import logging

from ceph_deploy import hosts, exc
from ceph_deploy.cliutil import priority


LOG = logging.getLogger(__name__)


def fetch_file(args, frompath, topath, _hosts):
    if os.path.exists(topath):
        LOG.debug('Have %s', topath)
        return True
    else:
        for hostname in _hosts:
            filepath = frompath.format(hostname=hostname)
            LOG.debug('Checking %s for %s', hostname, filepath)
            distro = hosts.get(hostname, username=args.username)
            key = distro.conn.remote_module.get_file(filepath)

            if key is not None:
                LOG.debug('Got %s key from %s.', topath, hostname)
                with file(topath, 'w') as f:
                    f.write(key)
                    return True
            distro.conn.exit()
            LOG.warning('Unable to find %s on %s', filepath, hostname)
    return False


def gatherkeys(args):
    oldmask = os.umask(077)
    try:
        # client.admin
        keyring = '/etc/ceph/{cluster}.client.admin.keyring'.format(
            cluster=args.cluster)
        r = fetch_file(
            args=args,
            frompath=keyring,
            topath='{cluster}.client.admin.keyring'.format(
                cluster=args.cluster),
            _hosts=args.mon,
            )
        if not r:
            raise exc.KeyNotFoundError(keyring, args.mon)

        # mon.
        keyring = '/var/lib/ceph/mon/{cluster}-{{hostname}}/keyring'.format(
            cluster=args.cluster)
        r = fetch_file(
            args=args,
            frompath=keyring,
            topath='{cluster}.mon.keyring'.format(cluster=args.cluster),
            _hosts=args.mon,
            )
        if not r:
            raise exc.KeyNotFoundError(keyring, args.mon)

        # bootstrap
        for what in ['osd', 'mds', 'rgw']:
            keyring = '/var/lib/ceph/bootstrap-{what}/{cluster}.keyring'.format(
                what=what,
                cluster=args.cluster)
            r = fetch_file(
                args=args,
                frompath=keyring,
                topath='{cluster}.bootstrap-{what}.keyring'.format(
                    cluster=args.cluster,
                    what=what),
                _hosts=args.mon,
                )
            if not r:
                if what in ['osd', 'mds']:
                    raise exc.KeyNotFoundError(keyring, args.mon)
                else:
                    LOG.warning(("No RGW bootstrap key found. Will not be able to "
                                 "deploy RGW daemons"))
    finally:
        os.umask(oldmask)

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
