import argparse
import json
import logging
import re
import os
from textwrap import dedent
import time

from ceph_deploy import conf, exc, admin
from ceph_deploy.cliutil import priority
from ceph_deploy.util import paths, net
from ceph_deploy.lib import remoto
from ceph_deploy import hosts
from ceph_deploy.misc import mon_hosts
from ceph_deploy.connection import get_connection
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
        return json.loads(''.join(out))
    except ValueError:
        return {}


def catch_mon_errors(conn, logger, hostname, cfg, args):
    """
    Make sure we are able to catch up common mishaps with monitors
    and use that state of a monitor to determine what is missing
    and warn apropriately about it.
    """
    monmap = mon_status_check(conn, logger, hostname, args).get('monmap', {})
    mon_initial_members = cfg.safe_get('global', 'mon_initial_members')
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


def mon_add(args):
    cfg = conf.ceph.load(args)

    if not args.mon:
        raise exc.NeedHostError()
    mon_host = args.mon[0]
    try:
        with file('{cluster}.mon.keyring'.format(cluster=args.cluster),
                  'rb') as f:
            monitor_keyring = f.read()
    except IOError:
        raise RuntimeError(
            'mon keyring not found; run \'new\' to create a new cluster'
        )

    LOG.info('ensuring configuration of new mon host: %s', mon_host)
    args.client = [mon_host]
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
        distro = hosts.get(mon_host, username=args.username)
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
        mon_initial_members = cfg.safe_get('global', 'mon_initial_members')
        args.mon = re.split(r'[,\s]+', mon_initial_members)

    if not args.mon:
        raise exc.NeedHostError()

    try:
        with file('{cluster}.mon.keyring'.format(cluster=args.cluster),
                  'rb') as f:
            monitor_keyring = f.read()
    except IOError:
        raise RuntimeError('mon keyring not found; run \'new\' to create a new cluster')

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
            distro = hosts.get(host, username=args.username)
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
        if conn.remote_module.path_exists(os.path.join(path, 'upstart')):
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

            distro = hosts.get(host, username=args.username)
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
    cfg = conf.ceph.load(args)
    cfg_initial_members = cfg.safe_get('global', 'mon_initial_members')
    if cfg_initial_members is None:
        raise RuntimeError('No `mon initial members` defined in config')
    mon_initial_members = re.split(r'[,\s]+', cfg_initial_members)

    # create them normally through mon_create
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
        rconn = get_connection(host, username=args.username, logger=rlogger)
        while tries:
            status = mon_status_check(rconn, rlogger, host, args)
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
        rconn.exit()

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
    Deploy ceph monitor on remote hosts.
    """
    sub_command_help = dedent("""
    Subcommands:

    create-initial
      Will deploy for monitors defined in `mon initial members`, wait until
      they form quorum and then gatherkeys, reporting the monitor status along
      the process. If monitors don't form quorum the command will eventually
      time out.

    create
      Deploy monitors by specifying them like:

        ceph-deploy mon create node1 node2 node3

      If no hosts are passed it will default to use the `mon initial members`
      defined in the configuration.

    add
      Add a monitor to an existing cluster:

        ceph-deploy mon add node1

      Or:

        ceph-deploy mon add node1 --address 192.168.1.10

      If the section for the monitor exists and defines a `mon addr` that
      will be used, otherwise it will fallback by resolving the hostname to an
      IP. If `--address` is used it will override all other options.

    destroy
      Completely remove monitors on a remote host. Requires hostname(s) as
      arguments.
    """)
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = sub_command_help

    parser.add_argument(
        'subcommand',
        choices=[
            'add',
            'create',
            'create-initial',
            'destroy',
            ],
        )

    parser.add_argument(
        '--address',
        nargs='?',
        dest='address',
    )

    parser.add_argument(
        'mon',
        nargs='*',
    )

    parser.set_defaults(
        func=mon,
    )

#
# Helpers
#


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
    result_string = ' '.join(stdout)
    for run_check in [': running', ' start/running']:
        if run_check in result_string:
            return True
    return False
