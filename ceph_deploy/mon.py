import json
import logging
import re
import os
import time

from ceph_deploy import conf, exc, admin
from ceph_deploy.cliutil import priority
from ceph_deploy.util.help_formatters import ToggleRawTextHelpFormatter
from ceph_deploy.util import paths, net, files, packages, system
from ceph_deploy.lib import remoto
from ceph_deploy.new import new_mon_keyring
from ceph_deploy import hosts
from ceph_deploy.misc import mon_hosts
from ceph_deploy import gatherkeys


LOG = logging.getLogger(__name__)


def mon_status_check(conn, logger, hostname, args):
    """
    A direct check for JSON output on the monitor status.

    For newer versions of Ceph (dumpling and newer) a new mon_status command
    was added ( `ceph daemon mon mon_status` ) and should be revisited if the
    output changes as this check depends on that availability.

    """
    asok_path = paths.mon.asok(args.cluster, hostname)

    out, err, code = remoto.process.check(
        conn,
        [
            'ceph',
            '--cluster={cluster}'.format(cluster=args.cluster),
            '--admin-daemon',
            asok_path,
            'mon_status',
        ],
    )

    for line in err:
        logger.error(line)

    try:
        return json.loads(b''.join(out).decode('utf-8'))
    except ValueError:
        return {}


def catch_mon_errors(conn, logger, hostname, cfg, args):
    """
    Make sure we are able to catch up common mishaps with monitors
    and use that state of a monitor to determine what is missing
    and warn apropriately about it.
    """
    monmap = mon_status_check(conn, logger, hostname, args).get('monmap', {})
    mon_initial_members = get_mon_initial_members(args, _cfg=cfg)
    public_addr = cfg.safe_get('global', 'public_addr')
    public_network = cfg.safe_get('global', 'public_network')
    mon_in_monmap = [
        mon.get('name')
        for mon in monmap.get('mons', [{}])
        if mon.get('name') == hostname
    ]
    if mon_initial_members is None or not hostname in mon_initial_members:
            logger.warning('%s is not defined in `mon initial members`', hostname)
    if not mon_in_monmap:
        logger.warning('monitor %s does not exist in monmap', hostname)
        if not public_addr and not public_network:
            logger.warning('neither `public_addr` nor `public_network` keys are defined for monitors')
            logger.warning('monitors may not be able to form quorum')


def mon_status(conn, logger, hostname, args, silent=False):
    """
    run ``ceph daemon mon.`hostname` mon_status`` on the remote end and provide
    not only the output, but be able to return a boolean status of what is
    going on.
    ``False`` represents a monitor that is not doing OK even if it is up and
    running, while ``True`` would mean the monitor is up and running correctly.
    """
    mon = 'mon.%s' % hostname

    try:
        out = mon_status_check(conn, logger, hostname, args)
        if not out:
            logger.warning('monitor: %s, might not be running yet' % mon)
            return False

        if not silent:
            logger.debug('*'*80)
            logger.debug('status for monitor: %s' % mon)
            for line in json.dumps(out, indent=2, sort_keys=True).split('\n'):
                logger.debug(line)
            logger.debug('*'*80)
        if out['rank'] >= 0:
            logger.info('monitor: %s is running' % mon)
            return True
        if out['rank'] == -1 and out['state']:
            logger.info('monitor: %s is currently at the state of %s' % (mon, out['state']))
            return True
        logger.info('monitor: %s is not running' % mon)
        return False
    except RuntimeError:
        logger.info('monitor: %s is not running' % mon)
        return False


def keyring_parser(path):
    """
    This is a very, very, dumb parser that will look for `[entity]` sections
    and return a list of those sections. It is not possible to parse this with
    ConfigParser even though it is almost the same thing.

    Since this is only used to spit out warnings, it is OK to just be naive
    about the parsing.
    """
    sections = []
    with open(path) as keyring:
        lines = keyring.readlines()
        for line in lines:
            line = line.strip('\n')
            if line.startswith('[') and line.endswith(']'):
                sections.append(line.strip('[]'))
    return sections


def concatenate_keyrings(args):
    """
    A helper to collect all keyrings into a single blob that will be
    used to inject it to mons with ``--mkfs`` on remote nodes

    We require all keyring files to be concatenated to be in a directory
    to end with ``.keyring``.
    """
    keyring_path = os.path.abspath(args.keyrings)
    LOG.info('concatenating keyrings from %s' % keyring_path)
    LOG.info('to seed remote monitors')

    keyrings = [
        os.path.join(keyring_path, f) for f in os.listdir(keyring_path)
        if os.path.isfile(os.path.join(keyring_path, f)) and f.endswith('.keyring')
    ]

    contents = []
    seen_sections = {}

    if not keyrings:
        path_from_arg = os.path.abspath(args.keyrings)
        raise RuntimeError('could not find any keyrings in %s' % path_from_arg)

    for keyring in keyrings:
        path = os.path.abspath(keyring)

        for section in keyring_parser(path):
            if not seen_sections.get(section):
                seen_sections[section] = path
                LOG.info('adding entity "%s" from keyring %s' % (section, path))
                with open(path) as k:
                    contents.append(k.read())
            else:
                LOG.warning('will not add keyring: %s' % path)
                LOG.warning('entity "%s" from keyring %s is a duplicate' % (section, path))
                LOG.warning('already present in keyring: %s' % seen_sections[section])

    return ''.join(contents)


def mon_add(args):
    cfg = conf.ceph.load(args)

    # args.mon is a list with only one entry
    mon_host = args.mon[0]

    try:
        with open('{cluster}.mon.keyring'.format(cluster=args.cluster),
                  'rb') as f:
            monitor_keyring = f.read()
    except IOError:
        raise RuntimeError(
            'mon keyring not found; run \'new\' to create a new cluster'
        )

    LOG.info('ensuring configuration of new mon host: %s', mon_host)
    args.client = args.mon
    admin.admin(args)
    LOG.debug(
        'Adding mon to cluster %s, host %s',
        args.cluster,
        mon_host,
    )

    mon_section = 'mon.%s' % mon_host
    cfg_mon_addr = cfg.safe_get(mon_section, 'mon addr')

    if args.address:
        LOG.debug('using mon address via --address %s' % args.address)
        mon_ip = args.address
    elif cfg_mon_addr:
        LOG.debug('using mon address via configuration: %s' % cfg_mon_addr)
        mon_ip = cfg_mon_addr
    else:
        mon_ip = net.get_nonlocal_ip(mon_host)
        LOG.debug('using mon address by resolving host: %s' % mon_ip)

    try:
        LOG.debug('detecting platform for host %s ...', mon_host)
        distro = hosts.get(
            mon_host,
            username=args.username,
            callbacks=[packages.ceph_is_installed]
        )
        LOG.info('distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(mon_host)

        # ensure remote hostname is good to go
        hostname_is_compatible(distro.conn, rlogger, mon_host)
        rlogger.debug('adding mon to %s', mon_host)
        args.address = mon_ip
        distro.mon.add(distro, args, monitor_keyring)

        # tell me the status of the deployed mon
        time.sleep(2)  # give some room to start
        catch_mon_errors(distro.conn, rlogger, mon_host, cfg, args)
        mon_status(distro.conn, rlogger, mon_host, args)
        distro.conn.exit()

    except RuntimeError as e:
        LOG.error(e)
        raise exc.GenericError('Failed to add monitor to host:  %s' % mon_host)


def mon_create(args):

    cfg = conf.ceph.load(args)
    if not args.mon:
        args.mon = get_mon_initial_members(args, error_on_empty=True, _cfg=cfg)

    if args.keyrings:
        monitor_keyring = concatenate_keyrings(args)
    else:
        keyring_path = '{cluster}.mon.keyring'.format(cluster=args.cluster)
        try:
            monitor_keyring = files.read_file(keyring_path)
        except IOError:
            LOG.warning('keyring (%s) not found, creating a new one' % keyring_path)
            new_mon_keyring(args)
            monitor_keyring = files.read_file(keyring_path)

    LOG.debug(
        'Deploying mon, cluster %s hosts %s',
        args.cluster,
        ' '.join(args.mon),
        )

    errors = 0
    for (name, host) in mon_hosts(args.mon):
        try:
            # TODO add_bootstrap_peer_hint
            LOG.debug('detecting platform for host %s ...', name)
            distro = hosts.get(
                host,
                username=args.username,
                callbacks=[packages.ceph_is_installed]
            )
            LOG.info('distro info: %s %s %s', distro.name, distro.release, distro.codename)
            rlogger = logging.getLogger(name)

            # ensure remote hostname is good to go
            hostname_is_compatible(distro.conn, rlogger, name)
            rlogger.debug('deploying mon to %s', name)
            distro.mon.create(distro, args, monitor_keyring)

            # tell me the status of the deployed mon
            time.sleep(2)  # give some room to start
            mon_status(distro.conn, rlogger, name, args)
            catch_mon_errors(distro.conn, rlogger, name, cfg, args)
            distro.conn.exit()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d monitors' % errors)


def hostname_is_compatible(conn, logger, provided_hostname):
    """
    Make sure that the host that we are connecting to has the same value as the
    `hostname` in the remote host, otherwise mons can fail not reaching quorum.
    """
    logger.debug('determining if provided host has same hostname in remote')
    remote_hostname = conn.remote_module.shortname()
    if remote_hostname == provided_hostname:
        return
    logger.warning('*'*80)
    logger.warning('provided hostname must match remote hostname')
    logger.warning('provided hostname: %s' % provided_hostname)
    logger.warning('remote hostname: %s' % remote_hostname)
    logger.warning('monitors may not reach quorum and create-keys will not complete')
    logger.warning('*'*80)


def destroy_mon(conn, cluster, hostname):
    import datetime
    import time
    retries = 5

    path = paths.mon.path(cluster, hostname)

    if conn.remote_module.path_exists(path):
        # remove from cluster
        remoto.process.run(
            conn,
            [
                'ceph',
                '--cluster={cluster}'.format(cluster=cluster),
                '-n', 'mon.',
                '-k', '{path}/keyring'.format(path=path),
                'mon',
                'remove',
                hostname,
            ],
            timeout=7,
        )

        # stop
        if conn.remote_module.path_exists(os.path.join(path, 'upstart')) or system.is_upstart(conn):
            status_args = [
                'initctl',
                'status',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=cluster),
                'id={hostname}'.format(hostname=hostname),
            ]

        elif conn.remote_module.path_exists(os.path.join(path, 'sysvinit')):
            status_args = [
                'service',
                'ceph',
                'status',
                'mon.{hostname}'.format(hostname=hostname),
            ]
        elif system.is_systemd(conn):
            status_args = [
                'systemctl',
                'stop',
                'ceph-mon@{hostname}.service'.format(hostname=hostname),
            ]
        else:
            raise RuntimeError('could not detect a supported init system, cannot continue')

        while retries:
            conn.logger.info('polling the daemon to verify it stopped')
            if is_running(conn, status_args):
                time.sleep(5)
                retries -= 1
                if retries <= 0:
                    raise RuntimeError('ceph-mon deamon did not stop')
            else:
                break

        # archive old monitor directory
        fn = '{cluster}-{hostname}-{stamp}'.format(
            hostname=hostname,
            cluster=cluster,
            stamp=datetime.datetime.utcnow().strftime("%Y-%m-%dZ%H:%M:%S"),
            )

        remoto.process.run(
            conn,
            [
                'mkdir',
                '-p',
                '/var/lib/ceph/mon-removed',
            ],
        )

        conn.remote_module.make_mon_removed_dir(path, fn)


def mon_destroy(args):
    errors = 0
    for (name, host) in mon_hosts(args.mon):
        try:
            LOG.debug('Removing mon from %s', name)

            distro = hosts.get(
                host,
                username=args.username,
                callbacks=[packages.ceph_is_installed]
            )
            hostname = distro.conn.remote_module.shortname()

            destroy_mon(
                distro.conn,
                args.cluster,
                hostname,
            )
            distro.conn.exit()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to destroy %d monitors' % errors)


def mon_create_initial(args):
    mon_initial_members = get_mon_initial_members(args, error_on_empty=True)

    # create them normally through mon_create
    args.mon = mon_initial_members
    mon_create(args)

    # make the sets to be able to compare late
    mon_in_quorum = set([])
    mon_members = set([host for host in mon_initial_members])

    for host in mon_initial_members:
        mon_name = 'mon.%s' % host
        LOG.info('processing monitor %s', mon_name)
        sleeps = [20, 20, 15, 10, 10, 5]
        tries = 5
        rlogger = logging.getLogger(host)
        distro = hosts.get(
            host,
            username=args.username,
            callbacks=[packages.ceph_is_installed]
        )

        while tries:
            status = mon_status_check(distro.conn, rlogger, host, args)
            has_reached_quorum = status.get('state', '') in ['peon', 'leader']
            if not has_reached_quorum:
                LOG.warning('%s monitor is not yet in quorum, tries left: %s' % (mon_name, tries))
                tries -= 1
                sleep_seconds = sleeps.pop()
                LOG.warning('waiting %s seconds before retrying', sleep_seconds)
                time.sleep(sleep_seconds)  # Magic number
            else:
                mon_in_quorum.add(host)
                LOG.info('%s monitor has reached quorum!', mon_name)
                break
        distro.conn.exit()

    if mon_in_quorum == mon_members:
        LOG.info('all initial monitors are running and have formed quorum')
        LOG.info('Running gatherkeys...')
        gatherkeys.gatherkeys(args)
    else:
        LOG.error('Some monitors have still not reached quorum:')
        for host in mon_members - mon_in_quorum:
            LOG.error('%s', host)
        raise SystemExit('cluster may not be in a healthy state')


def mon(args):
    if args.subcommand == 'create':
        mon_create(args)
    elif args.subcommand == 'add':
        mon_add(args)
    elif args.subcommand == 'destroy':
        mon_destroy(args)
    elif args.subcommand == 'create-initial':
        mon_create_initial(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)


@priority(30)
def make(parser):
    """
    Ceph MON Daemon management
    """
    parser.formatter_class = ToggleRawTextHelpFormatter

    mon_parser = parser.add_subparsers(dest='subcommand')
    mon_parser.required = True

    mon_add = mon_parser.add_parser(
        'add',
        help=('R|Add a monitor to an existing cluster:\n'
              '\tceph-deploy mon add node1\n'
              'Or:\n'
              '\tceph-deploy mon add --address 192.168.1.10 node1\n'
              'If the section for the monitor exists and defines a `mon addr` that\n'
              'will be used, otherwise it will fallback by resolving the hostname to an\n'
              'IP. If `--address` is used it will override all other options.')
    )
    mon_add.add_argument(
        '--address',
        nargs='?',
    )
    mon_add.add_argument(
        'mon',
        nargs=1,
    )

    mon_create = mon_parser.add_parser(
        'create',
        help=('R|Deploy monitors by specifying them like:\n'
              '\tceph-deploy mon create node1 node2 node3\n'
              'If no hosts are passed it will default to use the\n'
              '`mon initial members` defined in the configuration.')
    )
    mon_create.add_argument(
        '--keyrings',
        nargs='?',
        help='concatenate multiple keyrings to be seeded on new monitors',
    )
    mon_create.add_argument(
        'mon',
        nargs='*',
    )

    mon_create_initial = mon_parser.add_parser(
        'create-initial',
        help=('Will deploy for monitors defined in `mon initial members`, '
              'wait until they form quorum and then gatherkeys, reporting '
              'the monitor status along the process. If monitors don\'t form '
              'quorum the command will eventually time out.')
    )
    mon_create_initial.add_argument(
        '--keyrings',
        nargs='?',
        help='concatenate multiple keyrings to be seeded on new monitors',
    )

    mon_destroy = mon_parser.add_parser(
        'destroy',
        help='Completely remove Ceph MON from remote host(s)'
    )
    mon_destroy.add_argument(
        'mon',
        nargs='+',
    )

    parser.set_defaults(
        func=mon,
    )

#
# Helpers
#


def get_mon_initial_members(args, error_on_empty=False, _cfg=None):
    """
    Read the Ceph config file and return the value of mon_initial_members
    Optionally, a NeedHostError can be raised if the value is None.
    """
    if _cfg:
        cfg = _cfg
    else:
        cfg = conf.ceph.load(args)
    mon_initial_members = cfg.safe_get('global', 'mon_initial_members')
    if not mon_initial_members:
        if error_on_empty:
            raise exc.NeedHostError(
                'could not find `mon initial members` defined in ceph.conf'
            )
    else:
        mon_initial_members = re.split(r'[,\s]+', mon_initial_members)
    return mon_initial_members


def is_running(conn, args):
    """
    Run a command to check the status of a mon, return a boolean.

    We heavily depend on the format of the output, if that ever changes
    we need to modify this.
    Check daemon status for 3 times
    output of the status should be similar to::

        mon.mira094: running {"version":"0.61.5"}

    or when it fails::

        mon.mira094: dead {"version":"0.61.5"}
        mon.mira094: not running {"version":"0.61.5"}
    """
    stdout, stderr, _ = remoto.process.check(
        conn,
        args
    )
    result_string = b' '.join(stdout)
    for run_check in [b': running', b' start/running']:
        if run_check in result_string:
            return True
    return False
