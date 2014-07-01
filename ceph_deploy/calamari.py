import errno
import logging
import os
from ceph_deploy import hosts, exc
from ceph_deploy.lib import remoto


LOG = logging.getLogger(__name__)


def distro_is_supported(distro_name):
    """
    An enforcer of supported distros that can differ from what ceph-deploy
    supports.
    """
    supported = ['centos', 'redhat', 'ubuntu', 'debian']
    if distro_name in supported:
        return True
    return False


def connect(args):
    cd_conf = getattr(args, 'cd_conf', None)
    if not cd_conf:
        raise RuntimeError(
            'a ceph-deploy configuration is required but was not found'
        )

    repo_name = args.release or 'calamari-minion'
    has_minion_repo = cd_conf.has_section(repo_name)

    if not has_minion_repo:
        raise RuntimeError('no calamari-minion repo found')

    for hostname in args.hosts:
        distro = hosts.get(hostname, username=args.username)
        if not distro_is_supported(distro.normalized_name):
            raise exc.UnsupportedPlatform(
                distro.distro_name,
                distro.codename,
                distro.release
            )

        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        # We rely on the default for repo installs that does not install ceph
        # unless specified otherwise. We define the `options` dictionary here
        # because ceph-deploy pops items iternally and that causes issues when
        # those items need to be available for every host
        options = dict(cd_conf.items(repo_name))

        rlogger = logging.getLogger(hostname)
        if distro.name in ('debian', 'ubuntu'):
            rlogger.info('ensuring proxy is disabled for calamari minions repo')
            distro.conn.remote_module.write_file(
                '/etc/apt/apt.conf.d/99ceph',
                'Acquire::http::Proxy::%s DIRECT;' % args.master,
            )
        rlogger.info('installing calamari-minion package on %s' % hostname)
        rlogger.info('adding custom repository file')
        try:
            distro.repo_install(
                distro,
                repo_name,
                options.pop('baseurl'),
                options.pop('gpgkey', ''),  # will probably not use a gpgkey
                **options
            )
        except KeyError as err:
            raise RuntimeError(
                'missing required key: %s in config section: %s' % (
                    err,
                    repo_name
                )
            )

        # Emplace minion config prior to installation so that it is present
        # when the minion first starts.
        minion_config_dir = os.path.join('/etc/salt/', 'minion.d')
        minion_config_file = os.path.join(minion_config_dir, 'calamari.conf')

        rlogger.debug('creating config dir: %s' % minion_config_dir)
        distro.conn.remote_module.makedir(minion_config_dir, [errno.EEXIST])

        rlogger.debug(
            'creating the calamari salt config: %s' % minion_config_file
        )
        distro.conn.remote_module.write_file(
            minion_config_file,
            'master: %s\n' % args.master
        )

        distro.pkg.install(distro, 'salt-minion')

        # redhat/centos need to get the service started
        if distro.normalized_name in ['redhat', 'centos']:
            remoto.process.run(
                distro.conn,
                ['chkconfig', 'salt-minion', 'on']
            )

            remoto.process.run(
                distro.conn,
                ['service', 'salt-minion', 'start']
            )

        distro.conn.exit()


def calamari(args):
    if args.subcommand == 'connect':
        connect(args)


def make(parser):
    """
    Install and configure Calamari nodes
    """
    parser.add_argument(
        'subcommand',
        choices=[
            'connect',
            ],
        )

    parser.add_argument(
        '--release',
        nargs='?',
        metavar='CODENAME',
        help="Use a given release from repositories\
                defined in ceph-deploy's configuration. Defaults to\
                'calamari-minion'",

    )

    parser.add_argument(
        '--master',
        nargs='?',
        metavar='MASTER SERVER',
        help="The domain for the Calamari master server"
    )

    parser.add_argument(
        'hosts',
        nargs='+',
    )

    parser.set_defaults(
        func=calamari,
    )
