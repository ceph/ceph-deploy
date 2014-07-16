import argparse
import json
import logging
import os
import re
import sys
import time
from textwrap import dedent

from cStringIO import StringIO

from ceph_deploy import conf, exc, hosts
from ceph_deploy.util import constants, system
from ceph_deploy.cliutil import priority
from ceph_deploy.lib import remoto


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

    return remoto.process.run(
        conn,
        [
            'udevadm',
            'trigger',
            '--subsystem-match=block',
            '--action=add',
        ],
    )


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
        loaded_json = json.loads(''.join(out))
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
    command = [
        'ceph',
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
        loaded_json = json.loads(''.join(out))
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
        'ceph-disk',
        '-v',
        'prepare',
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

    remoto.process.run(
        conn,
        args
    )

    if activate_prepared_disk:
        return remoto.process.run(
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

        remoto.process.run(
            distro.conn,
            [
                'ceph-disk',
                '-v',
                'activate',
                '--mark-init',
                distro.init,
                '--mount',
                disk,
            ],
        )
        # give the OSD a few seconds to start
        time.sleep(5)
        catch_osd_errors(distro.conn, distro.conn.logger, args)
        distro.conn.exit()


def disk_zap(args):

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

        distro.conn.remote_module.zeroing(disk)

        ceph_disk_executable = system.executable_path(distro.conn, 'ceph-disk')
        remoto.process.run(
            distro.conn,
            [
                ceph_disk_executable,
                'zap',
                disk,
            ],
        )

        # once all is done, call partprobe (or partx)
        # On RHEL and CentOS distros, calling partprobe forces a reboot of the
        # server. Since we are not resizing partitons we rely on calling
        # partx
        if distro.normalized_name.startswith(('centos', 'red')):
            LOG.info('calling partx on zapped device %s', disk)
            LOG.info('re-reading known partitions will display errors')
            remoto.process.run(
                distro.conn,
                [
                    'partx',
                    '-a',
                    disk,
                ],
            )

        else:
            LOG.debug('Calling partprobe on zapped device %s', disk)
            remoto.process.run(
                distro.conn,
                [
                    'partprobe',
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
        ceph_disk_executable = system.executable_path(distro.conn, 'ceph-disk')
        remoto.process.run(
            distro.conn,
            [
                ceph_disk_executable,
                'list',
            ],
        )
        distro.conn.exit()


def osd_list(args, cfg):
    # FIXME: this portion should probably be abstracted. We do the same in
    # mon.py
    cfg = conf.ceph.load(args)
    mon_initial_members = cfg.safe_get('global', 'mon_initial_members')
    monitors = re.split(r'[,\s]+', mon_initial_members)

    if not monitors:
        raise exc.NeedHostError(
            'could not find `mon initial members` defined in ceph.conf'
        )

    # get the osd tree from a monitor host
    mon_host = monitors[0]
    distro = hosts.get(mon_host, username=args.username)
    tree = osd_tree(distro.conn, args.cluster)
    distro.conn.exit()

    interesting_files = ['active', 'magic', 'whoami', 'journal_uuid']

    for hostname, disk, journal in args.disk:
        distro = hosts.get(hostname, username=args.username)
        remote_module = distro.conn.remote_module
        osds = distro.conn.remote_module.listdir(constants.osd_path)

        ceph_disk_executable = system.executable_path(distro.conn, 'ceph-disk')
        output, err, exit_code = remoto.process.check(
            distro.conn,
            [
                ceph_disk_executable,
                'list',
            ]
        )

        for _osd in osds:
            osd_path = os.path.join(constants.osd_path, _osd)
            journal_path = os.path.join(osd_path, 'journal')
            _id = int(_osd.split('-')[-1])  # split on dash, get the id
            osd_name = 'osd.%s' % _id
            metadata = {}
            json_blob = {}

            # piggy back from ceph-disk and get the mount point
            device = get_osd_mount_point(output, osd_name)
            if device:
                metadata['device'] = device

            # read interesting metadata from files
            for f in interesting_files:
                osd_f_path = os.path.join(osd_path, f)
                if remote_module.path_exists(osd_f_path):
                    metadata[f] = remote_module.readline(osd_f_path)

            # do we have a journal path?
            if remote_module.path_exists(journal_path):
                metadata['journal path'] = remote_module.get_realpath(journal_path)

            # is this OSD in osd tree?
            for blob in tree['nodes']:
                if blob.get('id') == _id:  # matches our OSD
                    json_blob = blob

            print_osd(
                distro.conn.logger,
                hostname,
                osd_path,
                json_blob,
                metadata,
            )

        distro.conn.exit()


def get_osd_mount_point(output, osd_name):
    """
    piggy back from `ceph-disk list` output and get the mount point
    by matching the line where the partition mentions the OSD name

    For example, if the name of the osd is `osd.1` and the output from
    `ceph-disk list` looks like this::

        /dev/sda :
         /dev/sda1 other, ext2, mounted on /boot
         /dev/sda2 other
         /dev/sda5 other, LVM2_member
        /dev/sdb :
         /dev/sdb1 ceph data, active, cluster ceph, osd.1, journal /dev/sdb2
         /dev/sdb2 ceph journal, for /dev/sdb1
        /dev/sr0 other, unknown
        /dev/sr1 other, unknown

    Then `/dev/sdb1` would be the right mount point. We piggy back like this
    because ceph-disk does *a lot* to properly calculate those values and we
    don't want to re-implement all the helpers for this.

    :param output: A list of lines from stdout
    :param osd_name: The actual osd name, like `osd.1`
    """
    for line in output:
        line_parts = re.split(r'[,\s]+', line)
        for part in line_parts:
            mount_point = line_parts[1]
            if osd_name == part:
                return mount_point


def print_osd(logger, hostname, osd_path, json_blob, metadata, journal=None):
    """
    A helper to print OSD metadata
    """
    logger.info('-'*40)
    logger.info('%s' % osd_path.split('/')[-1])
    logger.info('-'*40)
    logger.info('%-14s %s' % ('Path', osd_path))
    logger.info('%-14s %s' % ('ID', json_blob.get('id')))
    logger.info('%-14s %s' % ('Name', json_blob.get('name')))
    logger.info('%-14s %s' % ('Status', json_blob.get('status')))
    logger.info('%-14s %s' % ('Reweight', json_blob.get('reweight')))
    if journal:
        logger.info('Journal: %s' % journal)
    for k, v in metadata.items():
        #logger.info("%s: %-8s" % (k.capitalize(), v))
        logger.info("%-13s  %s" % (k.capitalize(), v))

    logger.info('-'*40)


def osd(args):
    cfg = conf.ceph.load(args)

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
    cfg = conf.ceph.load(args)

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
