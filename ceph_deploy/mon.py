import ConfigParser
import logging
import re
import subprocess

from cStringIO import StringIO

from . import conf
from . import exc
from . import lsb
from .cliutil import priority
from .sudo_pushy import get_transport
from .util import paths


LOG = logging.getLogger(__name__)


def create_mon(cluster, monitor_keyring, init, **kw):
    # These modules are imported here because this is a function that gets
    # compiled and sent over for remote execution
    os = kw.get('os', __import__('os'))
    socket = kw.get('socket', __import__('socket'))
    subprocess = kw.get('subprocess', __import__('subprocess'))
    paths = kw.get('paths')  # noqa

    hostname = socket.gethostname().split('.')[0]
    path = paths.mon.path(cluster, hostname)
    done_path = paths.mon.done(cluster, hostname)
    init_path = paths.mon.init(cluster, hostname, init)

    if not os.path.exists(path):
        os.makedirs(path)

    if not os.path.exists(done_path):
        if not os.path.exists(paths.mon.constants.tmp_path):
            os.makedirs(paths.mon.constants.tmp_path)
        keyring = paths.mon.keyring(cluster, hostname)

        with file(keyring, 'w') as f:
            f.write(monitor_keyring)

        subprocess.check_call(
            args=[
                'ceph-mon',
                '--cluster', cluster,
                '--mkfs',
                '-i', hostname,
                '--keyring', keyring,
                ],
            )
        os.unlink(keyring)
        with file(done_path, 'w'):
            pass

    if not os.path.exists(init_path):
        with file(init_path, 'w'):
            pass

    if init == 'upstart':
        subprocess.check_call(
            args=[
                'initctl',
                'emit',
                'ceph-mon',
                'cluster={cluster}'.format(cluster=cluster),
                'id={hostname}'.format(hostname=hostname),
                ],
            )
    elif init == 'sysvinit':
        subprocess.check_call(
            args=[
                'service',
                'ceph',
                'start',
                'mon.{hostname}'.format(hostname=hostname),
                ],
            )


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
            LOG.debug('Deploying mon to %s', hostname)

            # TODO username
            sudo = args.pushy(get_transport(hostname))

            (distro, release, codename) = lsb.get_lsb_release(sudo)
            init = lsb.choose_init(distro, codename)
            LOG.debug('Distro %s codename %s, will use %s',
                      distro, codename, init)

            write_conf_r = sudo.compile(conf.write_conf)
            conf_data = StringIO()
            cfg.write(conf_data)
            write_conf_r(
                cluster=args.cluster,
                conf=conf_data.getvalue(),
                overwrite=args.overwrite_conf,
                )

            create_mon_r = sudo.compile(create_mon)
            create_mon_r(
                cluster=args.cluster,
                monitor_keyring=monitor_keyring,
                init=init,
                paths=paths,
                )

            # TODO add_bootstrap_peer_hint

            sudo.close()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d monitors' % errors)


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
