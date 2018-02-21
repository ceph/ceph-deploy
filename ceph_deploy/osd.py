import argparse
import json
import logging
import sys
import time
from textwrap import dedent

from ceph_deploy import conf, exc, hosts
from ceph_deploy.util import system, packages
from ceph_deploy.cliutil import priority
from ceph_deploy.lib import remoto


LOG = logging.getLogger(__name__)


def get_bootstrap_osd_key(cluster):
    """
    Read the bootstrap-osd key for `cluster`.
    """
    path = '{cluster}.bootstrap-osd.keyring'.format(cluster=cluster)
    try:
        with open(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-osd keyring not found; run \'gatherkeys\'')


def create_osd_keyring(conn, cluster, key):
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


def osd_tree(conn, cluster):
    """
    Check the status of an OSD. Make sure all are up and in

    What good output would look like::

        {
            "epoch": 8,
            "num_osds": 1,
            "num_up_osds": 1,
            "num_in_osds": "1",
            "full": "false",
            "nearfull": "false"
        }

    Note how the booleans are actually strings, so we need to take that into
    account and fix it before returning the dictionary. Issue #8108
    """
    ceph_executable = system.executable_path(conn, 'ceph')
    command = [
        ceph_executable,
        '--cluster={cluster}'.format(cluster=cluster),
        'osd',
        'tree',
        '--format=json',
    ]

    out, err, code = remoto.process.check(
        conn,
        command,
    )

    try:
        loaded_json = json.loads(b''.join(out).decode('utf-8'))
        # convert boolean strings to actual booleans because
        # --format=json fails to do this properly
        for k, v in loaded_json.items():
            if v == 'true':
                loaded_json[k] = True
            elif v == 'false':
                loaded_json[k] = False
        return loaded_json
    except ValueError:
        return {}


def osd_status_check(conn, cluster):
    """
    Check the status of an OSD. Make sure all are up and in

    What good output would look like::

        {
            "epoch": 8,
            "num_osds": 1,
            "num_up_osds": 1,
            "num_in_osds": "1",
            "full": "false",
            "nearfull": "false"
        }

    Note how the booleans are actually strings, so we need to take that into
    account and fix it before returning the dictionary. Issue #8108
    """
    ceph_executable = system.executable_path(conn, 'ceph')
    command = [
        ceph_executable,
        '--cluster={cluster}'.format(cluster=cluster),
        'osd',
        'stat',
        '--format=json',
    ]

    try:
        out, err, code = remoto.process.check(
            conn,
            command,
        )
    except TypeError:
        # XXX This is a bug in remoto. If the other end disconnects with a timeout
        # it will return a None, and here we are expecting a 3 item tuple, not a None
        # so it will break with a TypeError. Once remoto fixes this, we no longer need
        # this try/except.
        return {}

    try:
        loaded_json = json.loads(b''.join(out).decode('utf-8'))
        # convert boolean strings to actual booleans because
        # --format=json fails to do this properly
        for k, v in loaded_json.items():
            if v == 'true':
                loaded_json[k] = True
            elif v == 'false':
                loaded_json[k] = False
        return loaded_json
    except ValueError:
        return {}


def catch_osd_errors(conn, logger, args):
    """
    Look for possible issues when checking the status of an OSD and
    report them back to the user.
    """
    logger.info('checking OSD status...')
    status = osd_status_check(conn, args.cluster)
    osds = int(status.get('num_osds', 0))
    up_osds = int(status.get('num_up_osds', 0))
    in_osds = int(status.get('num_in_osds', 0))
    full = status.get('full', False)
    nearfull = status.get('nearfull', False)

    if osds > up_osds:
        difference = osds - up_osds
        logger.warning('there %s %d OSD%s down' % (
            ['is', 'are'][difference != 1],
            difference,
            "s"[difference == 1:])
        )

    if osds > in_osds:
        difference = osds - in_osds
        logger.warning('there %s %d OSD%s out' % (
            ['is', 'are'][difference != 1],
            difference,
            "s"[difference == 1:])
        )

    if full:
        logger.warning('OSDs are full!')

    if nearfull:
        logger.warning('OSDs are near full!')


def create_osd(
        conn,
        cluster,
        data,
        journal,
        zap,
        fs_type,
        dmcrypt,
        dmcrypt_dir,
        storetype,
        block_wal,
        block_db,
        **kw):
    """
    Run on osd node, creates an OSD from a data disk.
    """
    ceph_volume_executable = system.executable_path(conn, 'ceph-volume')
    args = [
        ceph_volume_executable,
        '--cluster', cluster,
        'lvm',
        'create',
        '--%s' % storetype,
        '--data', data
    ]
    if zap:
        LOG.warning('zapping is no longer supported when preparing')
    if dmcrypt:
        args.append('--dmcrypt')
        # TODO: re-enable dmcrypt support once ceph-volume grows it
        LOG.warning('dmcrypt is currently not supported')

    if storetype == 'bluestore':
        if block_wal:
            args.append('--block.wal')
            args.append(block_wal)
        if block_db:
            args.append('--block.db')
            args.append(block_db)
    elif storetype == 'filestore':
        if not journal:
            raise RuntimeError('A journal lv or GPT partition must be specified when using filestore')
        args.append('--journal')
        args.append(journal)

    if kw.get('debug'):
        remoto.process.run(
            conn,
            args,
            env={'CEPH_VOLUME_DEBUG': '1'}
        )

    else:
        remoto.process.run(
            conn,
            args
        )


def create(args, cfg, create=False):
    if not args.host:
        raise RuntimeError('Required host was not specified as a positional argument')
    LOG.debug(
        'Creating OSD on cluster %s with data device %s',
        args.cluster,
        args.data
        )

    key = get_bootstrap_osd_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    hostname = args.host

    try:
        if args.data is None:
            raise exc.NeedDiskError(hostname)

        distro = hosts.get(
            hostname,
            username=args.username,
            callbacks=[packages.ceph_is_installed]
        )
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        if hostname not in bootstrapped:
            bootstrapped.add(hostname)
            LOG.debug('Deploying osd to %s', hostname)

            conf_data = conf.ceph.load_raw(args)
            distro.conn.remote_module.write_conf(
                args.cluster,
                conf_data,
                args.overwrite_conf
            )

            create_osd_keyring(distro.conn, args.cluster, key)

        # default to bluestore unless explicitly told not to
        storetype = 'bluestore'
        if args.filestore:
            storetype = 'filestore'

        create_osd(
            distro.conn,
            cluster=args.cluster,
            data=args.data,
            journal=args.journal,
            zap=args.zap_disk,
            fs_type=args.fs_type,
            dmcrypt=args.dmcrypt,
            dmcrypt_dir=args.dmcrypt_key_dir,
            storetype=storetype,
            block_wal=args.block_wal,
            block_db=args.block_db,
            debug=args.debug,
        )

        # give the OSD a few seconds to start
        time.sleep(5)
        catch_osd_errors(distro.conn, distro.conn.logger, args)
        LOG.debug('Host %s is now ready for osd use.', hostname)
        distro.conn.exit()

    except RuntimeError as e:
        LOG.error(e)
        errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d OSDs' % errors)


def disk_zap(args):

    hostname = args.host
    for disk in args.disk:
        if not disk or not hostname:
            raise RuntimeError('zap command needs both HOSTNAME and DISK but got "%s %s"' % (hostname, disk))
        LOG.debug('zapping %s on %s', disk, hostname)
        distro = hosts.get(
            hostname,
            username=args.username,
            callbacks=[packages.ceph_is_installed]
        )
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        distro.conn.remote_module.zeroing(disk)

        ceph_volume_executable = system.executable_path(distro.conn, 'ceph-volume')
        if args.debug:
            remoto.process.run(
                distro.conn,
                [
                    ceph_volume_executable,
                    'lvm',
                    'zap',
                    disk,
                ],
                env={'CEPH_VOLUME_DEBUG': '1'}
            )
        else:
            remoto.process.run(
                distro.conn,
                [
                    ceph_volume_executable,
                    'lvm',
                    'zap',
                    disk,
                ],
            )

        distro.conn.exit()


def disk_list(args, cfg):
    command = ['fdisk', '-l']

    for hostname in args.host:
        distro = hosts.get(
            hostname,
            username=args.username,
            callbacks=[packages.ceph_is_installed]
        )
        out, err, code = remoto.process.check(
            distro.conn,
            command,
        )
        for line in out:
            if line.startswith('Disk /'):
                distro.conn.logger.info(line)


def osd_list(args, cfg):
    for hostname in args.host:
        distro = hosts.get(
            hostname,
            username=args.username,
            callbacks=[packages.ceph_is_installed]
        )
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        LOG.debug('Listing disks on {hostname}...'.format(hostname=hostname))
        ceph_volume_executable = system.executable_path(distro.conn, 'ceph-volume')
        if args.debug:
            remoto.process.run(
                distro.conn,
                [
                    ceph_volume_executable,
                    'lvm',
                    'list',
                ],
                env={'CEPH_VOLUME_DEBUG': '1'}

            )
        else:
            remoto.process.run(
                distro.conn,
                [
                    ceph_volume_executable,
                    'lvm',
                    'list',
                ],
            )
        distro.conn.exit()


def osd(args):
    cfg = conf.ceph.load(args)

    if args.subcommand == 'list':
        osd_list(args, cfg)
    elif args.subcommand == 'create':
        create(args, cfg)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)


def disk(args):
    cfg = conf.ceph.load(args)

    if args.subcommand == 'list':
        disk_list(args, cfg)
    elif args.subcommand == 'create':
        create(args, cfg)
    elif args.subcommand == 'zap':
        disk_zap(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)


@priority(50)
def make(parser):
    """
    Prepare a data disk on remote host.
    """
    sub_command_help = dedent("""
    Create OSDs from a data disk on a remote host:

        ceph-deploy osd create {node} --data /path/to/device

    For bluestore, optional devices can be used::

        ceph-deploy osd create {node} --data /path/to/data --block-db /path/to/db-device
        ceph-deploy osd create {node} --data /path/to/data --block-wal /path/to/wal-device
        ceph-deploy osd create {node} --data /path/to/data --block-db /path/to/db-device --block-wal /path/to/wal-device

    For filestore, the journal must be specified, as well as the objectstore::

        ceph-deploy osd create {node} --filestore --data /path/to/data --journal /path/to/journal

    For data devices, it can be an existing logical volume in the format of:
    vg/lv, or a device. For other OSD components like wal, db, and journal, it
    can be logical volume (in vg/lv format) or it must be a GPT partition.
    """
    )
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = sub_command_help

    osd_parser = parser.add_subparsers(dest='subcommand')
    osd_parser.required = True

    osd_list = osd_parser.add_parser(
        'list',
        help='List OSD info from remote host(s)'
        )
    osd_list.add_argument(
        'host',
        nargs='+',
        metavar='HOST',
        help='remote host(s) to list OSDs from'
        )
    osd_list.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode on remote ceph-volume calls',
        )
    osd_create = osd_parser.add_parser(
        'create',
        help='Create new Ceph OSD daemon by preparing and activating a device'
    )
    osd_create.add_argument(
        '--data',
        metavar='DATA',
        help='The OSD data logical volume (vg/lv) or absolute path to device'
    )
    osd_create.add_argument(
        '--journal',
        help='Logical Volume (vg/lv) or path to GPT partition',
        )
    osd_create.add_argument(
        '--zap-disk',
        action='store_true',
        help='DEPRECATED - cannot zap when creating an OSD'
    )
    osd_create.add_argument(
        '--fs-type',
        metavar='FS_TYPE',
        choices=['xfs',
                 'btrfs'
                 ],
        default='xfs',
        help='filesystem to use to format DEVICE (xfs, btrfs)',
        )
    osd_create.add_argument(
        '--dmcrypt',
        action='store_true',
        help='use dm-crypt on DEVICE',
        )
    osd_create.add_argument(
        '--dmcrypt-key-dir',
        metavar='KEYDIR',
        default='/etc/ceph/dmcrypt-keys',
        help='directory where dm-crypt keys are stored',
        )
    osd_create.add_argument(
        '--filestore',
        action='store_true', default=None,
        help='filestore objectstore',
        )
    osd_create.add_argument(
        '--bluestore',
        action='store_true', default=None,
        help='bluestore objectstore',
        )
    osd_create.add_argument(
        '--block-db',
        default=None,
        help='bluestore block.db path'
        )
    osd_create.add_argument(
        '--block-wal',
        default=None,
        help='bluestore block.wal path'
        )
    osd_create.add_argument(
        'host',
        nargs='?',
        metavar='HOST',
        help='Remote host to connect'
        )
    osd_create.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode on remote ceph-volume calls',
        )
    parser.set_defaults(
        func=osd,
        )


@priority(50)
def make_disk(parser):
    """
    Manage disks on a remote host.
    """
    disk_parser = parser.add_subparsers(dest='subcommand')
    disk_parser.required = True

    disk_zap = disk_parser.add_parser(
        'zap',
        help='destroy existing data and filesystem on LV or partition',
        )
    disk_zap.add_argument(
        'host',
        nargs='?',
        metavar='HOST',
        help='Remote HOST(s) to connect'
        )
    disk_zap.add_argument(
        'disk',
        nargs='+',
        metavar='DISK',
        help='Disk(s) to zap'
        )
    disk_zap.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode on remote ceph-volume calls',
        )
    disk_list = disk_parser.add_parser(
        'list',
        help='List disk info from remote host(s)'
        )
    disk_list.add_argument(
        'host',
        nargs='+',
        metavar='HOST',
        help='Remote HOST(s) to list OSDs from'
        )
    disk_list.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode on remote ceph-volume calls',
        )
    parser.set_defaults(
        func=disk,
        )
