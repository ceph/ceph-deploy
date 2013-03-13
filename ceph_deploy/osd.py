import ConfigParser
import argparse
import logging
import os.path
import re
import sys

from cStringIO import StringIO

from . import conf
from . import exc
from . import lsb
from .cliutil import priority
from .memoize import memoize


log = logging.getLogger(__name__)


def get_bootstrap_osd_key(cluster):
    """
    Read the bootstrap-osd key for `cluster`.
    """
    path = '{cluster}.bootstrap-osd.keyring'.format(cluster=cluster)
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-osd keyring not found; run \'gatherkeys\'')

def create_osd(cluster, key):
    """
    Run on osd node, writes the bootstrap key if not there yet.

    Returns None on success, error message on error exceptions. pushy
    mangles exceptions to all be of type ExceptionProxy, so we can't
    tell between bug and correctly handled failure, so avoid using
    exceptions for non-exceptional runs.
    """
    import os
    import subprocess

    path = '/var/lib/ceph/bootstrap-osd/{cluster}.keyring'.format(
        cluster=cluster,
        )
    if not os.path.exists(path):
        tmp = '{path}.{pid}.tmp'.format(
            path=path,
            pid=os.getpid(),
            )
        # file() doesn't let us control access mode from the
        # beginning, and thus would have a race where attacker can
        # open before we chmod the file, so play games with os.open
        fd = os.open(
            tmp,
            (os.O_WRONLY|os.O_CREAT|os.O_EXCL
             |os.O_NOCTTY|os.O_NOFOLLOW),
            0600,
            )
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
            f.flush()
            os.fsync(f)
        os.rename(tmp, path)

    # in case disks have been prepared before we do this, activate
    # them now
    subprocess.check_call(
        args=[
            'udevadm',
            'trigger',
            '--subsystem-match=block',
            '--action=add',
            ],
        )


def prepare_disk(cluster, disk, journal, activate, zap, dmcrypt, dmcrypt_dir):
    """
    Run on osd node, prepares a data disk for use.
    """
    import subprocess

    args=[
        'ceph-disk-prepare',
        ]
    if zap:
        args.append('--zap-disk')
    if dmcrypt:
        args.append('--dmcrypt')
        if dmcrypt_dir is not None:
            args.append('--dmcrypt-key-dir')
            args.append(dmcrypt_dir)
    args.extend([
            '--',
            disk,
            ])
    if journal is not None:
        args.append(journal)
    subprocess.check_call(args=args)

    if activate:
        subprocess.check_call(
            args=[
                'udevadm',
                'trigger',
                '--subsystem-match=block',
                '--action=add',
                ],
            )


def activate_disk(cluster, disk, init):
    """
    Run on the osd node, activates a disk.
    """
    import subprocess

    subprocess.check_call(
        args=[
            'ceph-disk-activate',
            '--mark-init',
            init,
            '--mount',
            disk,
            ])


def prepare(args, cfg, activate):
    log.debug(
        'Preparing cluster %s disks %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.disk),
        )

    key = get_bootstrap_osd_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    for hostname, disk, journal in args.disk:
        try:
            # TODO username
            sudo = args.pushy('ssh+sudo:{hostname}'.format(
                    hostname=hostname,
                    ))

            if hostname not in bootstrapped:
                bootstrapped.add(hostname)
                log.debug('Deploying osd to %s', hostname)

                write_conf_r = sudo.compile(conf.write_conf)
                conf_data = StringIO()
                cfg.write(conf_data)
                write_conf_r(
                    cluster=args.cluster,
                    conf=conf_data.getvalue(),
                    overwrite=args.overwrite_conf,
                    )

                create_osd_r = sudo.compile(create_osd)
                error = create_osd_r(
                    cluster=args.cluster,
                    key=key,
                    )
                if error is not None:
                    raise exc.GenericError(error)
                log.debug('Host %s is now ready for osd use.', hostname)

            log.debug('Preparing host %s disk %s journal %s activate %s',
                      hostname, disk, journal, activate)

            prepare_disk_r = sudo.compile(prepare_disk)
            prepare_disk_r(
                cluster=args.cluster,
                disk=disk,
                journal=journal,
                activate=activate,
                zap=args.zap_disk,
                dmcrypt=args.dmcrypt,
                dmcrypt_dir=args.dmcrypt_key_dir,
                )

        except RuntimeError as e:
            log.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d OSDs' % errors)

def activate(args, cfg):
    log.debug(
        'Activating cluster %s disks %s',
        args.cluster,
        ' '.join(':'.join(t) for t in args.disk),
        )

    for hostname, disk, journal in args.disk:

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(
                hostname=hostname,
                ))

        log.debug('Activating host %s disk %s', hostname, disk)

        lsb_release_r = sudo.compile(lsb.lsb_release)
        (distro, release, codename) = lsb_release_r()
        init = lsb.choose_init(distro, codename)
        log.debug('Distro %s codename %s, will use %s',
                  distro, codename, init)

        activate_disk_r = sudo.compile(activate_disk)
        activate_disk_r(
            cluster=args.cluster,
            disk=disk,
            init=init,
            )


def osd(args):
    cfg = conf.load(args)

    if args.subcommand == 'prepare':
        prepare(args, cfg, activate=False)
    if args.subcommand == 'create':
        prepare(args, cfg, activate=True)
    elif args.subcommand == 'activate':
        activate(args, cfg)
    else:
        log.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)


def colon_separated(s):
    journal = None
    if s.count(':') == 2:
        (host, disk, journal) = s.split(':')
    elif s.count(':') == 1:
        (host, disk) = s.split(':')
    else:
        raise argparse.ArgumentTypeError('must be in form HOST:DISK[:JOURNAL]')

    # allow just "sdb" to mean /dev/sdb
    disk = os.path.join('/dev', disk)
    if journal is not None:
        journal = os.path.join('/dev', journal)

    return (host, disk, journal)


@priority(50)
def make(parser):
    """
    Prepare a data disk on remote host.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'create',
            'prepare',
            'activate',
            'destroy',
            ],
        help='create (prepare+activate), prepare, activate, or destroy',
        )
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK[:JOURNAL]',
        type=colon_separated,
        help='host and disk to prepare',
        )
    parser.add_argument(
        '--zap-disk',
        action='store_true', default=None,
        help='destroy existing partition table and content for DISK',
        )
    parser.add_argument(
        '--dmcrypt',
        action='store_true', default=None,
        help='use dm-crypt on DISK',
        )
    parser.add_argument(
        '--dmcrypt-key-dir',
        metavar='KEYDIR',
        default='/etc/ceph/dmcrypt-keys',
        help='directory where dm-crypt keys are stored',
        )
    parser.set_defaults(
        func=osd,
        )
