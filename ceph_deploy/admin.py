import argparse
import logging
import os.path

from cStringIO import StringIO

from . import exc
from .cliutil import priority


log = logging.getLogger(__name__)

def write_file(path, content):
    try:
        with file(path, 'w') as f:
            f.write(content)
    except:
        pass        

def admin(args):
    try:
        with file('%s.conf' % args.cluster, 'rb') as f:
            conf = f.read()
    except:
        raise RuntimeError('%s.conf file not present' % args.cluster)
    try:
        with file('%s.client.admin.keyring' % args.cluster, 'rb') as f:
            keyring = f.read()
    except:
        raise RuntimeError('%s.client.admin.keyring not found' %
                           args.cluster)

    for hostname in args.client:
        log.debug('Pushing admin keys and conf to %s', hostname)
        sudo = args.pushy('ssh+sudo:{hostname}'.format(
                hostname=hostname,
                ))
        write_file_r = sudo.compile(write_file)
        error = write_file_r(
            '/etc/ceph/%s.conf' % args.cluster,
            conf
            )
        if error is not None:
            raise exc.GenericError(error)
        error = write_file_r(
            '/etc/ceph/%s.client.admin.keyring' % args.cluster,
            keyring
            )
        if error is not None:
            raise exc.GenericError(error)

@priority(70)
def make(parser):
    """
    Push configuration and client.admin key to a remote host.
    """
    parser.add_argument(
        'client',
        metavar='HOST',
        nargs='*',
        help='host to configure for ceph administration',
        )
    parser.set_defaults(
        func=admin,
        )
