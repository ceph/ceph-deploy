import argparse
import logging
import os

from .cliutil import priority


log = logging.getLogger(__name__)


def prepare_disk(cluster, disk):
    """
    Run on osd node, prepares a data disk for use.
    """
    import subprocess

    subprocess.check_call(
        args=[
            'ceph-disk-prepare',
            '--',
            disk,
            ],
        )

    subprocess.check_call(
        args=[
            'udevadm',
            'trigger',
            '--subsystem-match=block',
            '--action=add',
            ],
        )


def disk(args):
    log.debug(
        'Preparing cluster %s disks %s',
        args.cluster,
        ' '.join(':'.join(t) for t in args.disk),
        )

    for (hostname, disk) in args.disk:
        log.debug('Preparing host %s disk %s', hostname, disk)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(
                hostname=hostname,
                ))

        prepare_disk_r = sudo.compile(prepare_disk)
        prepare_disk_r(
            cluster=args.cluster,
            disk=disk,
            )


def colon_separated(s):
    try:
        (host, disk) = s.split(':', 1)
    except ValueError:
        raise argparse.ArgumentTypeError('must be in form HOST:DISK')

    # allow just "sdb" to mean /dev/sdb
    disk = os.path.join('/dev', disk)

    return (host, disk)


@priority(50)
def make(parser):
    """
    Prepare a data disk on remote host.
    """
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK',
        type=colon_separated,
        help='host and disk to prepare',
        )
    parser.set_defaults(
        func=disk,
        )
