import ConfigParser
import argparse
import logging
import os.path
import re

from cStringIO import StringIO

from . import conf
from . import exc
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

def write_conf(cluster, conf):
    import os

    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp = '{path}.{pid}.tmp'.format(path=path, pid=os.getpid())

    with file(tmp, 'w') as f:
        f.write(conf)
        f.flush()
        os.fsync(f)
    os.rename(tmp, path)


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


def prepare_disk(cluster, disk, journal):
    """
    Run on osd node, prepares a data disk for use.
    """
    import subprocess

    subprocess.check_call(
        args=[
            'ceph-disk-prepare',
            '--',
            disk,
            journal,
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


def osd(args):
    cfg = conf.load(args)

    log.debug(
        'Preparing cluster %s disks %s',
        args.cluster,
        ' '.join(':'.join(t) for t in args.disk),
        )

    key = get_bootstrap_osd_key(cluster=args.cluster)

    bootstrapped = set()
    for hostname, disk, journal in args.disk:

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(
                hostname=hostname,
                ))

        if hostname not in bootstrapped:
            bootstrapped.add(hostname)
            log.debug('Deploying osd to %s', hostname)

            write_conf_r = sudo.compile(write_conf)
            conf_data = StringIO()
            cfg.write(conf_data)
            write_conf_r(
                cluster=args.cluster,
                conf=conf_data.getvalue(),
                )

            create_osd_r = sudo.compile(create_osd)
            error = create_osd_r(
                cluster=args.cluster,
                key=key,
                )
            if error is not None:
                raise exc.GenericError(error)
            log.debug('Host %s is now ready for osd use.', hostname)

        log.debug('Preparing host %s disk %s journal %s', hostname, disk,
                  journal)

        prepare_disk_r = sudo.compile(prepare_disk)
        prepare_disk_r(
            cluster=args.cluster,
            disk=disk,
            journal=journal,
            )


def colon_separated(s):
    journal = None
    if s.count(':') == 2:
        (host, disk, journal) = s.split(':')
    elif s.count(':') == 1:
        (host, disk) = s.split(':')
    else:
        raise argparse.ArgumentTypeError('must be in form HOST:DISK[:JOURNAL]')

    if journal is None:
        journal = disk

    # allow just "sdb" to mean /dev/sdb
    disk = os.path.join('/dev', disk)
    journal = os.path.join('/dev', journal)

    return (host, disk, journal)


@priority(50)
def make(parser):
    """
    Prepare a data disk on remote host.
    """
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK[:JOURNAL]',
        type=colon_separated,
        help='host and disk to prepare',
        )
    parser.set_defaults(
        func=osd,
        )
