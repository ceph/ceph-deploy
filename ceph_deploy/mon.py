import argparse
import json
import logging
import re
import subprocess
import socket
from textwrap import dedent
import time

from . import conf, exc
from .cliutil import priority
from .sudo_pushy import get_transport
from .util import paths
from .lib.remoto import process
from . import hosts
from .misc import mon_hosts, remote_shortname
from .connection import get_connection
from . import gatherkeys


LOG = logging.getLogger(__name__)


def mon_status_check(conn, logger, hostname, exit=False):
    """
    A direct check for JSON output on the monitor status.

    For newer versions of Ceph (dumpling and newer) a new mon_status command
    was added ( `ceph daemon mon mon_status` ) and should be revisited if the
    output changes as this check depends on that availability.

    WARNING: this function requires the new connection object
    """
    mon = 'mon.%s' % hostname

    out, err, code = process.check(
        conn,
        [
            'ceph',
            '--admin-daemon',
            '/var/run/ceph/ceph-%s.asok' % mon,
            'mon_status',
        ],
        exit=exit
    )

    for line in err:
        logger.error(line)

    try:
        return json.loads(''.join(out))
    except ValueError:
        return {}


def catch_mon_errors(conn, logger, hostname, cfg):
    """
    Make sure we are able to catch up common mishaps with monitors
    and use that state of a monitor to determine what is missing
    and warn apropriately about it.
    """
    conn = conn or get_connection(hostname, logger=logger)
    monmap = mon_status_check(conn, logger, hostname).get('monmap', {})
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


def mon_status(conn, logger, hostname, silent=False):
    """
    run ``ceph daemon mon.`hostname` mon_status`` on the remote end and provide
    not only the output, but be able to return a boolean status of what is
    going on.
    ``False`` represents a monitor that is not doing OK even if it is up and
    running, while ``True`` would mean the monitor is up and running correctly.
    """
    mon = 'mon.%s' % hostname
    rconn = get_connection(hostname, logger=logger)

    try:
        out = mon_status_check(rconn, logger, hostname, exit=True)
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
        logger.info('monitor: %s is not running' % mon)
        return False
    except RuntimeError:
        logger.info('monitor: %s is not running' % mon)
        return False


def mon_create(args):

    cfg = conf.load(args)
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
            # TODO username
            # TODO add_bootstrap_peer_hint
            LOG.debug('detecting platform for host %s ...', name)
            distro = hosts.get(host)
            LOG.info('distro info: %s %s %s', distro.name, distro.release, distro.codename)
            rlogger = logging.getLogger(name)

            # ensure remote hostname is good to go
            hostname_is_compatible(distro.sudo_conn, rlogger, name)
            rlogger.debug('deploying mon to %s', name)
            distro.mon.create(distro, rlogger, args, monitor_keyring)

            # tell me the status of the deployed mon
            time.sleep(2)  # give some room to start
            # distro.sudo_conn.close() used to happen here but it made some
            # connections hang. This is terrible, and we should move on to stop
            # using pushy ASAP.  Connections are closed individually now before
            # starting the monitors
            mon_status(None, rlogger, name)
            catch_mon_errors(None, rlogger, name, cfg)

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
    remote_hostname = remote_shortname(conn.modules.socket)
    if remote_hostname == provided_hostname:
        return
    logger.warning('*'*80)
    logger.warning('provided hostname must match remote hostname')
    logger.warning('provided hostname: %s' % provided_hostname)
    logger.warning('remote hostname: %s' % remote_hostname)
    logger.warning('monitors may not reach quorum and create-keys will not complete')
    logger.warning('*'*80)


def destroy_mon(cluster, paths, is_running, hostname):
    import datetime
    import errno
    import os
    import subprocess  # noqa
    import time
    retries = 5

    path = paths.mon.path(cluster, hostname)

    if os.path.exists(path):
        # remove from cluster
        proc = subprocess.Popen(
            args=[
                'sudo',
                'ceph',
                '--cluster={cluster}'.format(cluster=cluster),
                '-n', 'mon.',
                '-k', '{path}/keyring'.format(path=path),
                'mon',
                'remove',
                hostname,
                ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            )
        out, err = proc.communicate()
        return_status = proc.wait()
        if return_status > 0:
            raise RuntimeError(err.strip())

        # stop
        if os.path.exists(os.path.join(path, 'upstart')):
            status_args = [
                'initctl',
                'status',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=cluster),
                'id={hostname}'.format(hostname=hostname),
            ]

        elif os.path.exists(os.path.join(path, 'sysvinit')):
            status_args = [
                'service',
                'ceph',
                'status',
                'mon.{hostname}'.format(hostname=hostname),
            ]

        while retries:
            if is_running(status_args):
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
        subprocess.check_call(
            args=[
                'mkdir',
                '-p',
                '/var/lib/ceph/mon-removed',
                ],
            )
        try:
            os.makedirs('/var/lib/ceph/mon-removed')
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
        os.rename(path, os.path.join('/var/lib/ceph/mon-removed/', fn))


def mon_destroy(args):
    errors = 0
    for (name, host) in mon_hosts(args.mon):
        try:
            LOG.debug('Removing mon from %s', name)

            # TODO username
            sudo = args.pushy(get_transport(host))
            hostname = remote_shortname(sudo.modules.socket)

            destroy_mon_r = sudo.compile(destroy_mon)
            destroy_mon_r(
                cluster=args.cluster,
                paths=paths,
                is_running=is_running,
                hostname=hostname,
                )
            sudo.close()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to destroy %d monitors' % errors)


def mon_create_initial(args):
    cfg = conf.load(args)
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
        rconn = get_connection(host, logger=rlogger)
        while tries:
            status = mon_status_check(rconn, rlogger, host)
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

    if mon_in_quorum == mon_members:
        LOG.info('all initial monitors are running and have formed quorum')
        LOG.info('Running gatherkeys...')
        gatherkeys.gatherkeys(args)
    else:
        LOG.error('Some monitors have still not reached quorum:')
        for host in mon_members - mon_in_quorum:
            LOG.error('%s', host)


def mon(args):
    if args.subcommand == 'create':
        mon_create(args)
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

    destroy
      Completely remove monitors on a remote host. Requires hostname(s) as
      arguments.
    """)
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = sub_command_help

    parser.add_argument(
        'subcommand',
        choices=[
            'create',
            'create-initial',
            'destroy',
            ],
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


def is_running(args):
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
    proc = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result = proc.communicate()
    result_string = ' '.join(result)
    for run_check in [': running', ' start/running']:
        if run_check in result_string:
            return True
    return False
