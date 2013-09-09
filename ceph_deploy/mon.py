import ConfigParser
import json
import logging
import re
import subprocess
import time

from . import conf
from . import exc
from .cliutil import priority
from .sudo_pushy import get_transport
from .util import paths, wrappers
from . import hosts


LOG = logging.getLogger(__name__)


def mon_status(conn, logger, hostname, silent=False):
    """
    run ``ceph daemon mon.`hostname` mon_status`` on the remote end and provide
    not only the output, but be able to return a boolean status of what is
    going on.
    ``False`` represents a monitor that is not doing OK even if it is up and
    running, while ``True`` would mean the monitor is up and running correctly.
    """
    mon = 'mon.%s' % hostname
    try:
        out, err, code = wrappers.Popen(
            conn,
            logger,
            ['ceph', 'daemon', mon, 'mon_status']
        )

        try:
            mon_info = json.loads(out)
        except ValueError:
            logger.warning('monitor: %s, might not be running yet' % mon)
            return False
        if not silent:
            logger.debug('*'*80)
            logger.debug('status for monitor: %s' % mon)
            for k, v in mon_info.items():
                logger.debug('%s: %s' % (k, v))
            logger.debug('*'*80)
        if mon_info['rank'] >= 0:
            return True
        return False
    except RuntimeError:
        return False


def mon_create(args):

    cfg = conf.load(args)
    if not args.mon:
        try:
            mon_initial_members = cfg.get('global', 'mon_initial_members')
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            pass
        else:
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
    for hostname in args.mon:
        try:
            # TODO username
            # TODO add_bootstrap_peer_hint
            LOG.debug('detecting platform for host %s ...', hostname)
            distro = hosts.get(hostname)
            LOG.info('distro info: %s %s %s', distro.name, distro.release, distro.codename)
            rlogger = logging.getLogger(hostname)

            # ensure remote hostname is good to go
            hostname_is_compatible(distro.sudo_conn, rlogger, hostname)
            rlogger.debug('deploying mon to %s', hostname)
            distro.mon.create(distro, rlogger, args, monitor_keyring)

            # tell me the status of the deployed mon
            time.sleep(2)  # give some room to start
            mon_status(distro.sudo_conn, rlogger, hostname)
            distro.sudo_conn.close()

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
    remote_hostname = conn.modules.socket.gethostname()
    if remote_hostname == provided_hostname:
        return
    logger.warning('*'*80)
    logger.warning('provided hostname must match remote hostname')
    logger.warning('provided hostname: %s' % provided_hostname)
    logger.warning('remote hostname: %s' % remote_hostname)
    logger.warning('monitors may not reach quorum and create-keys will not complete')
    logger.warning('*'*80)


def destroy_mon(cluster, paths, is_running):
    import datetime
    import errno
    import os
    import subprocess  # noqa
    import socket
    import time
    retries = 5

    hostname = socket.gethostname().split('.')[0]
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
    for hostname in args.mon:
        try:
            LOG.debug('Removing mon from %s', hostname)

            # TODO username
            sudo = args.pushy(get_transport(hostname))

            destroy_mon_r = sudo.compile(destroy_mon)
            destroy_mon_r(
                cluster=args.cluster,
                paths=paths,
                is_running=is_running,
                )
            sudo.close()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to destroy %d monitors' % errors)


def mon(args):
    if args.subcommand == 'create':
        mon_create(args)
    elif args.subcommand == 'destroy':
        mon_destroy(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)


@priority(30)
def make(parser):
    """
    Deploy ceph monitor on remote hosts.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'create',
            'destroy',
            ],
        help='create or destroy',
        )
    parser.add_argument(
        'mon',
        metavar='HOST',
        nargs='*',
        help='host to deploy on',
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
