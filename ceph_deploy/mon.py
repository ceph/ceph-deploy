import ConfigParser
import logging
import re

from cStringIO import StringIO

from . import conf
from . import exc
from . import lsb
from .cliutil import priority
from .sudo_pushy import get_transport
from .util import paths, constants


LOG = logging.getLogger(__name__)


def create_mon(cluster, monitor_keyring, init, paths, constants):
    import os
    import socket
    import subprocess

    hostname = socket.gethostname().split('.')[0]
    path = paths.mon.path(cluster, hostname)
    done_path = paths.mon.done(cluster, hostname)
    init_path = paths.mon.init(cluster, hostname, init)

    if not os.path.exists(path):
        os.makedirs(path)

    if not os.path.exists(done_path):
        if not os.path.exists(constants.tnp_path):
            os.makedirs(constants.tnp_path)
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
                constants=constants,
                )

            # TODO add_bootstrap_peer_hint

            sudo.close()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d monitors' % errors)


def destroy_mon(cluster, paths):
    import os
    import subprocess
    import socket

    hostname = socket.gethostname().split('.')[0]
    path = paths.mon.path(cluster, hostname)

    if os.path.exists(path):
        # remove from cluster
        subprocess.check_call(
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
            )

        # stop
        if os.path.exists(os.path.join(path, 'upstart')):
            subprocess.call(   # ignore initctl error when job not running
                args=[
                    'initctl',
                    'stop',
                    'ceph-mon',
                    'cluster={cluster}'.format(cluster=cluster),
                    'id={hostname}'.format(hostname=hostname),
                ],
            )
        elif os.path.exists(os.path.join(path, 'sysvinit')):
            subprocess.check_call(
                args=[
                    'service',
                    'ceph',
                    'stop',
                    'mon.{hostname}'.format(hostname=hostname),
                ],
            )

        # delete monitor directory
        subprocess.check_call(
            args=[
                'rm',
                '-rf',
                path,
                ],
            )


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
                )
            sudo.close()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d monitors' % errors)


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
