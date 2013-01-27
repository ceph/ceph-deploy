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


log = logging.getLogger(__name__)


def generate_auth_key():
    key = os.urandom(16)
    header = struct.pack('<hiih',
                1,               # le16 type: CEPH_CRYPTO_AES
                int(time.time()),  # le32 created: seconds
                0,               # le32 created: nanoseconds,
                len(key),        # le16: len(key)
                )
    return base64.b64encode(header + key)

def new(args):
    log.debug('Creating new cluster named %s', args.cluster)
    cfg = ConfigParser.RawConfigParser()
    cfg.add_section('global')

    fsid = uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))

    if args.mon:
        mon_initial_members = []
        mon_host = []

        for m in args.mon:
            if m.count(':'):
                (name, host) = m.split(':')
            else:
                name = m
                host = m
            if name.count('.') > 0:
                name = name.split('.')[0]
            ip = socket.gethostbyname(host)
            log.debug('Monitor %s at %s', name, ip)
            mon_initial_members.append(name)
            mon_host.append(ip)

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

    tmp = '{name}.{pid}.tmp'.format(
        name=args.cluster,
        pid=os.getpid(),
        )
    path = '{name}.conf'.format(
        name=args.cluster,
        )

    # FIXME: create a random key
    log.debug('Creating a random mon key...')
    mon_keyring = '[mon.]\nkey = %s\ncaps mon = allow *\n' % generate_auth_key()

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
        os.unlink(tmp)

        with file(tmp, 'w') as f:
            f.write(mon_keyring)
        try:
            os.link(tmp, keypath)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise exc.ClusterExistsError(keypath)
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
    Start deploying a new cluster, and write a CLUSTER.conf and keyring for it.
    """
    parser.add_argument(
        'mon',
        metavar='MON',
        nargs='*',
        help='initial monitor hostname, fqdn, or hostname:fqdn pair',
        )
    parser.set_defaults(
        func=new,
        )
