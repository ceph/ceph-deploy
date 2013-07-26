import logging

from cStringIO import StringIO

from . import conf
from . import exc
from . import lsb
from .cliutil import priority
from .sudo_pushy import get_transport


LOG = logging.getLogger(__name__)


def get_bootstrap_mds_key(cluster):
    """
    Read the bootstrap-mds key for `cluster`.
    """
    path = '{cluster}.bootstrap-mds.keyring'.format(cluster=cluster)
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-mds keyring not found; run \'gatherkeys\'')


def create_mds_bootstrap(cluster, key):
    """
    Run on mds node, writes the bootstrap key if not there yet.

    Returns None on success, error message on error exceptions. pushy
    mangles exceptions to all be of type ExceptionProxy, so we can't
    tell between bug and correctly handled failure, so avoid using
    exceptions for non-exceptional runs.
    """
    import os

    path = '/var/lib/ceph/bootstrap-mds/{cluster}.keyring'.format(
        cluster=cluster,
        )
    if not os.path.exists(path):
        tmp = '{path}.{pid}.tmp'.format(
            path=path,
            pid=os.getpid(),
            )
        # file() doesn't let us control access mode from the
        # beginning, and thus would have a race where attacker can
        # open before we chmod the file, so play games with os.open
        fd = os.open(
            tmp,
            (os.O_WRONLY|os.O_CREAT|os.O_EXCL
             |os.O_NOCTTY|os.O_NOFOLLOW),
            0600,
            )
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
            f.flush()
            os.fsync(f)
        os.rename(tmp, path)


def create_mds(
    name,
    cluster,
    init,
    ):
    import os
    import subprocess
    import errno

    path = '/var/lib/ceph/mds/{cluster}-{name}'.format(
        cluster=cluster,
        name=name
        )

    try:
        os.mkdir(path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    bootstrap_keyring = '/var/lib/ceph/bootstrap-mds/{cluster}.keyring'.format(
        cluster=cluster
        )

    keypath = os.path.join(path, 'keyring')

    try:
        subprocess.check_call(
            args = [
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
                ])
    except subprocess.CalledProcessError as err:
        if err.returncode != errno.EACCES:
            raise
        subprocess.check_call(
            args = [
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
                ])

    with file(os.path.join(path, 'done'), 'wb') as f:
        pass

    with file(os.path.join(path, init), 'wb') as f:
        pass

    if init == 'upstart':
        subprocess.check_call(
            args=[
                'initctl',
                'emit',
                'ceph-mds',
                'cluster={cluster}'.format(cluster=cluster),
                'id={name}'.format(name=name),
                ])
    elif init == 'sysvinit':
        subprocess.check_call(
            args=[
                'service',
                'ceph',
                'start',
                'mds.{name}'.format(name=name),
                ])

def mds_create(args):
    cfg = conf.load(args)
    LOG.debug(
        'Deploying mds, cluster %s hosts %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.mds),
        )

    if not args.mds:
        raise exc.NeedHostError()

    key = get_bootstrap_mds_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    for hostname, name in args.mds:
        try:
            # TODO username
            sudo = args.pushy(get_transport(hostname))

            (distro, release, codename) = lsb.get_lsb_release(sudo)
            init = lsb.choose_init(distro, codename)
            LOG.debug('Distro %s codename %s, will use %s',
                      distro, codename, init)

            if hostname not in bootstrapped:
                bootstrapped.add(hostname)
                LOG.debug('Deploying mds bootstrap to %s', hostname)

                write_conf_r = sudo.compile(conf.write_conf)
                conf_data = StringIO()
                cfg.write(conf_data)
                write_conf_r(
                    cluster=args.cluster,
                    conf=conf_data.getvalue(),
                    overwrite=args.overwrite_conf,
                    )

                create_mds_bootstrap_r = sudo.compile(create_mds_bootstrap)
                error = create_mds_bootstrap_r(
                    cluster=args.cluster,
                    key=key,
                    )
                if error is not None:
                    raise exc.GenericError(error)
                LOG.debug('Host %s is now ready for MDS use.', hostname)

            # create an mds
            LOG.debug('Deploying mds.%s to %s', name, hostname)
            create_mds_r = sudo.compile(create_mds)
            create_mds_r(
                name=name,
                cluster=args.cluster,
                init=init,
                )
            sudo.close()
        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
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
    Deploy ceph MDS on remote hosts.
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
        'mds',
        metavar='HOST[:NAME]',
        nargs='*',
        type=colon_separated,
        help='host (and optionally the daemon name) to deploy on',
        )
    parser.set_defaults(
        func=mds,
        )
