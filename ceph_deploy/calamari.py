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
        LOG.info('assuming that a repository with Calamari packages is already configured.')
        LOG.info('Refer to the docs for examples (http://ceph.com/ceph-deploy/docs/conf.html)')

        rlogger = logging.getLogger(hostname)

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
            ('master: %s\n' % args.master).encode('utf-8')
        )

        distro.packager.install('salt-minion')
        distro.packager.install('diamond')

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
    Install and configure Calamari nodes. Assumes that a repository with
    Calamari packages is already configured. Refer to the docs for examples
    (http://ceph.com/ceph-deploy/docs/conf.html)
    """
    calamari_parser = parser.add_subparsers(dest='subcommand')
    calamari_parser.required = True

    calamari_connect = calamari_parser.add_parser(
        'connect',
        help='Configure host(s) to connect to Calamari master'
    )
    calamari_connect.add_argument(
        '--master',
        nargs='?',
        metavar='MASTER SERVER',
        help="The domain for the Calamari master server"
    )
    calamari_connect.add_argument(
        'hosts',
        nargs='+',
    )

    parser.set_defaults(
        func=calamari,
    )
