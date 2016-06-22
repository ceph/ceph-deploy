try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import errno
import logging
import os

from ceph_deploy import conf
from ceph_deploy import exc
from ceph_deploy import hosts
from ceph_deploy.util import system
from ceph_deploy.lib import remoto
from ceph_deploy.cliutil import priority


LOG = logging.getLogger(__name__)


def get_bootstrap_mds_key(cluster):
    """
    Read the bootstrap-mds key for `cluster`.
    """
    path = '{cluster}.bootstrap-mds.keyring'.format(cluster=cluster)
    try:
        with open(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-mds keyring not found; run \'gatherkeys\'')


def create_mds(distro, name, cluster, init):
    conn = distro.conn

    path = '/var/lib/ceph/mds/{cluster}-{name}'.format(
        cluster=cluster,
        name=name
        )

    conn.remote_module.safe_mkdir(path)

    bootstrap_keyring = '/var/lib/ceph/bootstrap-mds/{cluster}.keyring'.format(
        cluster=cluster
        )

    keypath = os.path.join(path, 'keyring')

    stdout, stderr, returncode = remoto.process.check(
        conn,
        [
            'ceph',
            '--cluster', cluster,
            '--name', 'client.bootstrap-mds',
            '--keyring', bootstrap_keyring,
            'auth', 'get-or-create', 'mds.{name}'.format(name=name),
            'osd', 'allow rwx',
            'mds', 'allow',
            'mon', 'allow profile mds',
            '-o',
            os.path.join(keypath),
        ]
    )
    if returncode > 0 and returncode != errno.EACCES:
        for line in stderr:
            conn.logger.error(line)
        for line in stdout:
            # yes stdout as err because this is an error
            conn.logger.error(line)
        conn.logger.error('exit code from command was: %s' % returncode)
        raise RuntimeError('could not create mds')

        remoto.process.check(
            conn,
            [
                'ceph',
                '--cluster', cluster,
                '--name', 'client.bootstrap-mds',
                '--keyring', bootstrap_keyring,
                'auth', 'get-or-create', 'mds.{name}'.format(name=name),
                'osd', 'allow *',
                'mds', 'allow',
                'mon', 'allow rwx',
                '-o',
                os.path.join(keypath),
            ]
        )

    conn.remote_module.touch_file(os.path.join(path, 'done'))
    conn.remote_module.touch_file(os.path.join(path, init))

    if init == 'upstart':
        remoto.process.run(
            conn,
            [
                'initctl',
                'emit',
                'ceph-mds',
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
                'mds.{name}'.format(name=name),
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
                'ceph-mds@{name}'.format(name=name),
            ],
            timeout=7
        )
        remoto.process.run(
            conn,
            [
                'systemctl',
                'start',
                'ceph-mds@{name}'.format(name=name),
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



def mds_create(args):
    cfg = conf.ceph.load(args)
    LOG.debug(
        'Deploying mds, cluster %s hosts %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.mds),
        )

    key = get_bootstrap_mds_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    failed_on_rhel = False

    for hostname, name in args.mds:
        try:
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
                LOG.debug('deploying mds bootstrap to %s', hostname)
                conf_data = StringIO()
                cfg.write(conf_data)
                distro.conn.remote_module.write_conf(
                    args.cluster,
                    conf_data.getvalue(),
                    args.overwrite_conf,
                )

                path = '/var/lib/ceph/bootstrap-mds/{cluster}.keyring'.format(
                    cluster=args.cluster,
                )

                if not distro.conn.remote_module.path_exists(path):
                    rlogger.warning('mds keyring does not exist yet, creating one')
                    distro.conn.remote_module.write_keyring(path, key)

            create_mds(distro, name, args.cluster, distro.init)
            distro.conn.exit()
        except RuntimeError as e:
            if distro.normalized_name == 'redhat':
                LOG.error('this feature may not yet available for %s %s' % (distro.name, distro.release))
                failed_on_rhel = True
            LOG.error(e)
            errors += 1

    if errors:
        if failed_on_rhel:
            # because users only read the last few lines :(
            LOG.error(
                'RHEL RHCS systems do not have the ability to deploy MDS yet'
            )

        raise exc.GenericError('Failed to create %d MDSs' % errors)


def mds(args):
    if args.subcommand == 'create':
        mds_create(args)
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
    Ceph MDS daemon management
    """
    mds_parser = parser.add_subparsers(dest='subcommand')
    mds_parser.required = True

    mds_create = mds_parser.add_parser(
        'create',
        help='Deploy Ceph MDS on remote host(s)'
    )
    mds_create.add_argument(
        'mds',
        metavar='HOST[:NAME]',
        nargs='+',
        type=colon_separated,
        help='host (and optionally the daemon name) to deploy on',
        )
    parser.set_defaults(
        func=mds,
        )
