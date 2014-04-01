import logging
from ceph_deploy import hosts, exc
from ceph_deploy.lib.remoto import process


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

    # We rely on the default for repo installs that does not
    # install ceph unless specified otherwise
    options = dict(cd_conf.items(repo_name))

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
        rlogger = logging.getLogger(hostname)
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

        distro.pkg.install(distro, 'salt-minion')

        # redhat/centos need to get the service started
        if distro.normalized_name in ['redhat', 'centos']:
            process.run(
                distro.conn,
                ['chkconfig', 'salt-minion', 'on']
            )

            process.run(
                distro.conn,
                ['service', 'salt-minion', 'start']
            )

        distro.conn.exit()


def action(args):
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
        'hosts',
        nargs='+',
    )

    parser.set_defaults(
        func=action,
    )
