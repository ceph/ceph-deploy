import ConfigParser
import errno
import logging
import os
import uuid
import struct
import time
import base64
import socket

from . import exc
from .cliutil import priority
from .util import arg_validators
from .misc import mon_hosts


LOG = logging.getLogger(__name__)


def generate_auth_key():
    key = os.urandom(16)
    header = struct.pack('<hiih',
                1,               # le16 type: CEPH_CRYPTO_AES
                int(time.time()),  # le32 created: seconds
                0,               # le32 created: nanoseconds,
                len(key),        # le16: len(key)
                )
    return base64.b64encode(header + key)

def get_nonlocal_ip(host):
    """
    Search result of getaddrinfo() for a non-localhost-net address
    """
    ailist = socket.getaddrinfo(host, None)
    for ai in ailist:
        # an ai is a 5-tuple; the last element is (ip, port)
        ip = ai[4][0]
        if not ip.startswith('127.'):
            return ip
    raise exc.UnableToResolveError(host)


def new(args):
    LOG.debug('Creating new cluster named %s', args.cluster)
    cfg = ConfigParser.RawConfigParser()
    cfg.add_section('global')

    fsid = uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))

    mon_initial_members = []
    mon_host = []

    for (name, host) in mon_hosts(args.mon):
        LOG.debug('Resolving host %s', host)
        ip = None
        ip = get_nonlocal_ip(host)
        LOG.debug('Monitor %s at %s', name, ip)
        mon_initial_members.append(name)
        mon_host.append(ip)

    LOG.debug('Monitor initial members are %s', mon_initial_members)
    LOG.debug('Monitor addrs are %s', mon_host)

    cfg.set('global', 'mon initial members', ', '.join(mon_initial_members))
    # no spaces here, see http://tracker.newdream.net/issues/3145
    cfg.set('global', 'mon host', ','.join(mon_host))

    # override undesirable defaults, needed until bobtail

    # http://tracker.newdream.net/issues/3136
    cfg.set('global', 'auth supported', 'cephx')

    # http://tracker.newdream.net/issues/3137
    cfg.set('global', 'osd journal size', '1024')

    # http://tracker.newdream.net/issues/3138
    cfg.set('global', 'filestore xattr use omap', 'true')

    path = '{name}.conf'.format(
        name=args.cluster,
        )

    # FIXME: create a random key
    LOG.debug('Creating a random mon key...')
    mon_keyring = '[mon.]\nkey = %s\ncaps mon = allow *\n' % generate_auth_key()

    keypath = '{name}.mon.keyring'.format(
        name=args.cluster,
        )

    LOG.debug('Writing initial config to %s...', path)
    if not args.dry_run:
        tmp = '%s.tmp' % path
        with file(tmp, 'w') as f:
            cfg.write(f)
        try:
            os.rename(tmp, path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise exc.ClusterExistsError(path)
            else:
                raise

    LOG.debug('Writing monitor keyring to %s...', keypath)
    if not args.dry_run:
        tmp = '%s.tmp' % keypath
        with file(tmp, 'w') as f:
            f.write(mon_keyring)
        try:
            os.rename(tmp, keypath)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise exc.ClusterExistsError(keypath)
            else:
                raise


@priority(10)
def make(parser):
    """
    Start deploying a new cluster, and write a CLUSTER.conf and keyring for it.
    """
    parser.add_argument(
        'mon',
        metavar='MON',
        nargs='+',
        help='initial monitor hostname, fqdn, or hostname:fqdn pair',
        type=arg_validators.Hostname(),
        )
    parser.set_defaults(
        func=new,
        )
