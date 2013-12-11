import argparse
import logging
import os
import sys
from textwrap import dedent

from cStringIO import StringIO

from . import conf
from . import exc
from . import hosts
from .cliutil import priority
from .lib.remoto import process
from ceph_deploy.util import paths
from ceph_deploy.util import info


LOG = logging.getLogger(__name__)


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


def create_osd(conn, cluster, key):
    """
    Run on osd node, writes the bootstrap key if not there yet.
    """
    logger = conn.logger
    path = '/var/lib/ceph/bootstrap-osd/{cluster}.keyring'.format(
        cluster=cluster,
        )
    if not conn.remote_module.path_exists(path):
        logger.warning('osd keyring does not exist yet, creating one')
        conn.remote_module.write_keyring(path, key)

    return process.run(
        conn,
        [
            'udevadm',
            'trigger',
            '--subsystem-match=block',
            '--action=add',
        ],
    )


def prepare_disk(
        conn,
        cluster,
        disk,
        journal,
        activate_prepared_disk,
        zap,
        fs_type,
        dmcrypt,
        dmcrypt_dir):
    """
    Run on osd node, prepares a data disk for use.
    """
    args = [
        'ceph-disk-prepare',
        ]
    if zap:
        args.append('--zap-disk')
    if fs_type:
        if fs_type not in ('btrfs', 'ext4', 'xfs'):
            raise argparse.ArgumentTypeError(
                "FS_TYPE must be one of 'btrfs', 'ext4' or 'xfs'")
        args.extend(['--fs-type', fs_type])
    if dmcrypt:
        args.append('--dmcrypt')
        if dmcrypt_dir is not None:
            args.append('--dmcrypt-key-dir')
            args.append(dmcrypt_dir)
    args.extend([
        '--cluster',
        cluster,
        '--',
        disk,
    ])

    if journal is not None:
        args.append(journal)

    process.run(
        conn,
        args
    )

    if activate_prepared_disk:
        return process.run(
            conn,
            [
                'udevadm',
                'trigger',
                '--subsystem-match=block',
                '--action=add',
            ],
        )


def prepare(args, cfg, activate_prepared_disk):
    LOG.debug(
        'Preparing cluster %s disks %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.disk),
        )

    key = get_bootstrap_osd_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    for hostname, disk, journal in args.disk:
        try:
            if disk is None:
                raise exc.NeedDiskError(hostname)

            distro = hosts.get(hostname, username=args.username)
            LOG.info(
                'Distro info: %s %s %s',
                distro.name,
                distro.release,
                distro.codename
            )

            if hostname not in bootstrapped:
                bootstrapped.add(hostname)
                LOG.debug('Deploying osd to %s', hostname)

                conf_data = StringIO()
                cfg.write(conf_data)
                distro.conn.remote_module.write_conf(
                    args.cluster,
                    conf_data.getvalue(),
                    args.overwrite_conf
                )

                create_osd(distro.conn, args.cluster, key)

            LOG.debug('Preparing host %s disk %s journal %s activate %s',
                      hostname, disk, journal, activate_prepared_disk)

            prepare_disk(
                distro.conn,
                cluster=args.cluster,
                disk=disk,
                journal=journal,
                activate_prepared_disk=activate_prepared_disk,
                zap=args.zap_disk,
                fs_type=args.fs_type,
                dmcrypt=args.dmcrypt,
                dmcrypt_dir=args.dmcrypt_key_dir,
            )

            LOG.debug('Host %s is now ready for osd use.', hostname)
            distro.conn.exit()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d OSDs' % errors)


def activate(args, cfg):
    LOG.debug(
        'Activating cluster %s disks %s',
        args.cluster,
        # join elements of t with ':', t's with ' '
        # allow None in elements of t; print as empty
        ' '.join(':'.join((s or '') for s in t) for t in args.disk),
        )

    for hostname, disk, journal in args.disk:

        distro = hosts.get(hostname, username=args.username)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        LOG.debug('activating host %s disk %s', hostname, disk)
        LOG.debug('will use init type: %s', distro.init)

        process.run(
            distro.conn,
            [
                'ceph-disk-activate',
                '--mark-init',
                distro.init,
                '--mount',
                disk,
            ],
        )

        distro.conn.exit()


def disk_zap(args):
    cfg = conf.load(args)

    for hostname, disk, journal in args.disk:
        if not disk or not hostname:
            raise RuntimeError('zap command needs both HOSTNAME and DISK but got "%s %s"' % (hostname, disk))
        LOG.debug('zapping %s on %s', disk, hostname)
        distro = hosts.get(hostname, username=args.username)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        # NOTE: this mirrors ceph-disk-prepare --zap-disk DEV
        # zero the device
        distro.conn.remote_module.zeroing(disk)

        process.run(
            distro.conn,
            [
                'sgdisk',
                '--zap-all',
                '--clear',
                '--mbrtogpt',
                '--',
                disk,
            ],
        )
        distro.conn.exit()


def disk_list(args, cfg):
    for hostname, disk, journal in args.disk:
        distro = hosts.get(hostname, username=args.username)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        LOG.debug('Listing disks on {hostname}...'.format(hostname=hostname))
        process.run(
            distro.conn,
            [
                'ceph-disk',
                'list',
            ],
        )
        distro.conn.exit()


def osd_list(args, cfg):

    osd_base = paths.osd.base()
    for hostname, disk, journal in args.disk:
        osds = []
        distro = hosts.get(hostname, username=args.username)

        LOG.debug('Listing osds on {hostname}...'.format(hostname=hostname))

        dir = distro.conn.remote_module.get_dir_info(osd_base, True, True)
        for file, typ, realfile in dir:
            osd = info.osd.osd_info()
            osd.datapath = os.path.join(osd_base, file)
            osd.datapathtyp = typ
            osd.realdatapath = realfile

            magic_path = os.path.join(osd_base, file, 'magic')
            if distro.conn.remote_module.path_exists(magic_path):
                osd.magic = (distro.conn.remote_module.get_file(magic_path)).rstrip()

            active_path = os.path.join(osd_base, file, 'active')
            if distro.conn.remote_module.path_exists(active_path):
                osd.active = (distro.conn.remote_module.get_file(active_path)).rstrip()

            whoami_path = os.path.join(osd_base, file, 'whoami')
            if distro.conn.remote_module.path_exists(whoami_path):
                osd.whoami = (distro.conn.remote_module.get_file(whoami_path)).rstrip()

            journal_path = os.path.join(osd_base, file, 'journal')
            if distro.conn.remote_module.path_exists(journal_path):
                osd.journalpath = journal_path
                osd.realjournalpath = distro.conn.remote_module.get_realpath(journal_path)

            if osd.active != None and osd.magic != None and osd.whoami != None:
                osds.append(osd)

        distro.conn.exit()

        for osd in osds:
            if osd.valid_whoami():
                LOG.info("osd.%s :", osd.whoami)
            else:
                LOG.warning("osd.%s : (osd number not valid)", osd.whoami)
            if osd.valid_datapath():
                LOG.info(" data    %s, %s, %s", osd.datapath, osd.datapathtyp, osd.realdatapath)
            else:
                LOG.warning(" data    %s, %s, %s (data does not match osd number)", osd.datapath, osd.datapathtyp, osd.realdatapath)
            if osd.valid_journal():
                LOG.info(" journal %s", osd.realjournalpath)
            else:
                LOG.warn(" journal %s (journal missing)", osd.realjournalpath)
            LOG.info(" magic   %s", osd.magic)
            LOG.info(" active  %s", osd.active)


def osd(args):
    cfg = conf.load(args)

    if args.subcommand == 'list':
        osd_list(args, cfg)
    elif args.subcommand == 'prepare':
        prepare(args, cfg, activate_prepared_disk=False)
    elif args.subcommand == 'create':
        prepare(args, cfg, activate_prepared_disk=True)
    elif args.subcommand == 'activate':
        activate(args, cfg)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)


def disk(args):
    cfg = conf.load(args)

    if args.subcommand == 'list':
        disk_list(args, cfg)
    elif args.subcommand == 'prepare':
        prepare(args, cfg, activate_prepared_disk=False)
    elif args.subcommand == 'activate':
        activate(args, cfg)
    elif args.subcommand == 'zap':
        disk_zap(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)


def colon_separated(s):
    journal = None
    disk = None
    host = None
    if s.count(':') == 2:
        (host, disk, journal) = s.split(':')
    elif s.count(':') == 1:
        (host, disk) = s.split(':')
    elif s.count(':') == 0:
        (host) = s
    else:
        raise argparse.ArgumentTypeError('must be in form HOST:DISK[:JOURNAL]')

    if disk:
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
    sub_command_help = dedent("""
    Manage OSDs by preparing a data disk on remote host.

    For paths, first prepare and then activate:

        ceph-deploy osd prepare {osd-node-name}:/path/to/osd
        ceph-deploy osd activate {osd-node-name}:/path/to/osd

    For disks or journals the `create` command will do prepare and activate
    for you.
    """
    )
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = sub_command_help

    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'list',
            'create',
            'prepare',
            'activate',
            'destroy',
            ],
        help='list, create (prepare+activate), prepare, activate, or destroy',
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
        '--fs-type',
        metavar='FS_TYPE',
        default='xfs',
        help='filesystem to use to format DISK (xfs, btrfs or ext4)',
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


@priority(50)
def make_disk(parser):
    """
    Manage disks on a remote host.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'list',
            'prepare',
            'activate',
            'zap',
            ],
        help='list, prepare, activate, zap',
        )
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK',
        type=colon_separated,
        help='host and disk (or path)',
        )
    parser.add_argument(
        '--zap-disk',
        action='store_true', default=None,
        help='destroy existing partition table and content for DISK',
        )
    parser.add_argument(
        '--fs-type',
        metavar='FS_TYPE',
        default='xfs',
        help='filesystem to use to format DISK (xfs, btrfs or ext4)'
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
        func=disk,
        )
