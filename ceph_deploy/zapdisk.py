import ConfigParser
import argparse
import logging
import os
import subprocess

from cStringIO import StringIO

from . import conf
from . import exc
from .cliutil import priority
from .memoize import memoize


log = logging.getLogger(__name__)


# NOTE: this mirrors ceph-disk-prepare --zap-disk DEV
def zap(dev):
    import subprocess

    try:
        # this kills the crab
        lba_size = 4096
        size = 33 * lba_size
        with file(dev, 'wb') as f:
            f.seek(-size, os.SEEK_END)
            f.write(size*'\0')

        subprocess.check_call(
            args=[
                'sgdisk',
                '--zap-all',
                '--clear',
                '--mbrtogpt',
                '--',
                dev,
                ],
            )
    except subprocess.CalledProcessError as e:
        raise PrepareError(e)

def zapdisk(args):
    cfg = conf.load(args)

    for hostname, disk in args.disk:
        log.debug('zapping %s on %s', disk, hostname)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(
                hostname=hostname,
                ))
        zap_r = sudo.compile(zap)
        zap_r(disk)

def colon_separated(s):
    journal = None
    if s.count(':') == 1:
        (host, disk) = s.split(':')
    else:
        raise argparse.ArgumentTypeError('must be in form HOST:DISK')

    # allow just "sdb" to mean /dev/sdb
    disk = os.path.join('/dev', disk)

    return (host, disk)


@priority(50)
def make(parser):
    """
    Zap a data disk on a remote host.
    """
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK',
        type=colon_separated,
        help='host and disk to zap',
        )
    parser.set_defaults(
        func=zapdisk,
        )
