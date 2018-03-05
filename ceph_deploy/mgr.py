import logging
import os

from ceph_deploy import conf
from ceph_deploy import exc
from ceph_deploy import hosts
from ceph_deploy.util import system
from ceph_deploy.lib import remoto
from ceph_deploy.cliutil import priority


LOG = logging.getLogger(__name__)


def get_bootstrap_mgr_key(cluster):
    """
    Read the bootstrap-mgr key for `cluster`.
    """
    path = '{cluster}.bootstrap-mgr.keyring'.format(cluster=cluster)
    try:
        with open(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-mgr keyring not found; run \'gatherkeys\'')


def create_mgr(distro, name, cluster, init):
    conn = distro.conn

    path = '/var/lib/ceph/mgr/{cluster}-{name}'.format(
        cluster=cluster,
        name=name
        )

    conn.remote_module.safe_makedirs(path)

    bootstrap_keyring = '/var/lib/ceph/bootstrap-mgr/{cluster}.keyring'.format(
        cluster=cluster
        )

    keypath = os.path.join(path, 'keyring')

    stdout, stderr, returncode = remoto.process.check(
        conn,
        [
            'ceph',
            '--cluster', cluster,
            '--name', 'client.bootstrap-mgr',
            '--keyring', bootstrap_keyring,
            'auth', 'get-or-create', 'mgr.{name}'.format(name=name),
            'mon', 'allow profile mgr',
            'osd', 'allow *',
            'mds', 'allow *',
            '-o',
            os.path.join(keypath),
        ]
    )
    if returncode > 0:
        for line in stderr:
            conn.logger.error(line)
        for line in stdout:
            # yes stdout as err because this is an error
            conn.logger.error(line)
        conn.logger.error('exit code from command was: %s' % returncode)
        raise RuntimeError('could not create mgr')

    conn.remote_module.touch_file(os.path.join(path, 'done'))
    conn.remote_module.touch_file(os.path.join(path, init))

    if init == 'upstart':
        remoto.process.run(
            conn,
            [
                'initctl',
                'emit',
                'ceph-mgr',
                'cluster={cluster}'.format(cluster=cluster),
                'id={name}'.format(name=name),
            ],
            timeout=7
        )
    elif init == 'sysvinit':
        remoto.process.run(
            conn,
            [
                'service',
                'ceph',
                'start',
                'mgr.{name}'.format(name=name),
            ],
            timeout=7
        )
        if distro.is_el:
            system.enable_service(distro.conn)
    elif init == 'systemd':
        remoto.process.run(
            conn,
            [
                'systemctl',
                'enable',
                'ceph-mgr@{name}'.format(name=name),
            ],
            timeout=7
        )
        remoto.process.run(
            conn,
            [
                'systemctl',
                'start',
                'ceph-mgr@{name}'.format(name=name),
            ],
            timeout=7
        )
        remoto.process.run(
            conn,
            [
                'systemctl',
                'enable',
                'ceph.target',
            ],
            timeout=7
        )



def mgr_create(args):
    conf_data = conf.ceph.load_raw(args)
    LOG.debug(
        'Deploying mgr, cluster %s hosts %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.mgr),
        )

    key = get_bootstrap_mgr_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    failed_on_rhel = False

    for hostname, name in args.mgr:
        try:
            distro = None
            distro = hosts.get(hostname, username=args.username)
            rlogger = distro.conn.logger
            LOG.info(
                'Distro info: %s %s %s',
                distro.name,
                distro.release,
                distro.codename
            )

            LOG.debug('remote host will use %s', distro.init)

            if hostname not in bootstrapped:
                bootstrapped.add(hostname)
                LOG.debug('deploying mgr bootstrap to %s', hostname)
                distro.conn.remote_module.write_conf(
                    args.cluster,
                    conf_data,
                    args.overwrite_conf,
                )

                path = '/var/lib/ceph/bootstrap-mgr/{cluster}.keyring'.format(
                    cluster=args.cluster,
                )

                if not distro.conn.remote_module.path_exists(path):
                    rlogger.warning('mgr keyring does not exist yet, creating one')
                    distro.conn.remote_module.write_keyring(path, key)

            create_mgr(distro, name, args.cluster, distro.init)
            distro.conn.exit()
        except RuntimeError as e:
            if distro and distro.normalized_name == 'redhat':
                LOG.error('this feature may not yet available for %s %s' % (distro.name, distro.release))
                failed_on_rhel = True
            LOG.error(e)
            errors += 1

    if errors:
        if failed_on_rhel:
            # because users only read the last few lines :(
            LOG.error(
                'RHEL RHCS systems do not have the ability to deploy MGR yet'
            )

        raise exc.GenericError('Failed to create %d MGRs' % errors)


def mgr(args):
    if args.subcommand == 'create':
        mgr_create(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)


def colon_separated(s):
    host = s
    name = s
    if s.count(':') == 1:
        (host, name) = s.split(':')
    return (host, name)


@priority(30)
def make(parser):
    """
    Ceph MGR daemon management
    """
    mgr_parser = parser.add_subparsers(dest='subcommand')
    mgr_parser.required = True

    mgr_create = mgr_parser.add_parser(
        'create',
        help='Deploy Ceph MGR on remote host(s)'
    )
    mgr_create.add_argument(
        'mgr',
        metavar='HOST[:NAME]',
        nargs='+',
        type=colon_separated,
        help='host (and optionally the daemon name) to deploy on',
        )
    parser.set_defaults(
        func=mgr,
        )
