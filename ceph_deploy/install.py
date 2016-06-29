import argparse
import logging
import os

from ceph_deploy import hosts
from ceph_deploy.cliutil import priority
from ceph_deploy.lib import remoto
from ceph_deploy.util.constants import default_components
from ceph_deploy.util.paths import gpg

LOG = logging.getLogger(__name__)


def sanitize_args(args):
    """
    args may need a bunch of logic to set proper defaults that argparse is
    not well suited for.
    """
    if args.release is None:
        args.release = 'jewel'
        args.default_release = True

    # XXX This whole dance is because --stable is getting deprecated
    if args.stable is not None:
        LOG.warning('the --stable flag is deprecated, use --release instead')
        args.release = args.stable
    # XXX Tango ends here.

    return args


def detect_components(args, distro):
    """
    Since the package split, now there are various different Ceph components to
    install like:

    * ceph
    * ceph-mon
    * ceph-osd
    * ceph-mds

    This helper function should parse the args that may contain specifics about
    these flags and return the default if none are passed in (which is, install
    everything)
    """
    # the flag that prevents all logic here is the `--repo` flag which is used
    # when no packages should be installed, just the repo files, so check for
    # that here and return an empty list (which is equivalent to say 'no
    # packages should be installed')
    if args.repo:
        return []

    flags = {
        'install_osd': 'ceph-osd',
        'install_rgw': 'ceph-radosgw',
        'install_mds': 'ceph-mds',
        'install_mon': 'ceph-mon',
        'install_common': 'ceph-common',
        'install_tests': 'ceph-test',
    }

    if distro.is_rpm:
        defaults = default_components.rpm
    else:
        defaults = default_components.deb
        # different naming convention for deb than rpm for radosgw
        flags['install_rgw'] = 'radosgw'

    if args.install_all:
        return defaults
    else:
        components = []
        for k, v in flags.items():
            if getattr(args, k, False):
                components.append(v)
        # if we have some components selected from flags then return that,
        # otherwise return defaults because no flags and no `--repo` means we
        # should get all of them by default
        return components or defaults


def install(args):
    args = sanitize_args(args)

    if args.repo:
        return install_repo(args)

    gpgcheck = 0 if args.nogpgcheck else 1

    if args.version_kind == 'stable':
        version = args.release
    else:
        version = getattr(args, args.version_kind)

    version_str = args.version_kind

    if version:
        version_str += ' version {version}'.format(version=version)
    LOG.debug(
        'Installing %s on cluster %s hosts %s',
        version_str,
        args.cluster,
        ' '.join(args.host),
    )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)
        distro = hosts.get(
            hostname,
            username=args.username,
            # XXX this should get removed once ceph packages are split for
            # upstream. If default_release is True, it means that the user is
            # trying to install on a RHEL machine and should expect to get RHEL
            # packages. Otherwise, it will need to specify either a specific
            # version, or repo, or a development branch. Other distro users
            # should not see any differences.
            use_rhceph=args.default_release,
            )
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        components = detect_components(args, distro)
        if distro.init == 'sysvinit' and args.cluster != 'ceph':
            LOG.error('refusing to install on host: %s, with custom cluster name: %s' % (
                    hostname,
                    args.cluster,
                )
            )
            LOG.error('custom cluster names are not supported on sysvinit hosts')
            continue

        rlogger = logging.getLogger(hostname)
        rlogger.info('installing Ceph on %s' % hostname)

        cd_conf = getattr(args, 'cd_conf', None)

        # custom repo arguments
        repo_url = os.environ.get('CEPH_DEPLOY_REPO_URL') or args.repo_url
        gpg_url = os.environ.get('CEPH_DEPLOY_GPG_URL') or args.gpg_url
        gpg_fallback = gpg.url('release')

        if gpg_url is None and repo_url:
            LOG.warning('--gpg-url was not used, will fallback')
            LOG.warning('using GPG fallback: %s', gpg_fallback)
            gpg_url = gpg_fallback

        if args.local_mirror:
            if args.username:
                hostname = "%s@%s" % (args.username, hostname)
            remoto.rsync(hostname, args.local_mirror, '/opt/ceph-deploy/repo', distro.conn.logger, sudo=True)
            repo_url = 'file:///opt/ceph-deploy/repo'
            gpg_url = 'file:///opt/ceph-deploy/repo/release.asc'

        if repo_url:  # triggers using a custom repository
            # the user used a custom repo url, this should override anything
            # we can detect from the configuration, so warn about it
            if cd_conf:
                if cd_conf.get_default_repo():
                    rlogger.warning('a default repo was found but it was \
                        overridden on the CLI')
                if args.release in cd_conf.get_repos():
                    rlogger.warning('a custom repo was found but it was \
                        overridden on the CLI')

            rlogger.info('using custom repository location: %s', repo_url)
            distro.mirror_install(
                distro,
                repo_url,
                gpg_url,
                args.adjust_repos,
                components=components,
                gpgcheck=gpgcheck,
            )

        # Detect and install custom repos here if needed
        elif should_use_custom_repo(args, cd_conf, repo_url):
            LOG.info('detected valid custom repositories from config file')
            custom_repo(distro, args, cd_conf, rlogger)

        else:  # otherwise a normal installation
            distro.install(
                distro,
                args.version_kind,
                version,
                args.adjust_repos,
                components=components,
                gpgcheck = gpgcheck,
            )

        # Check the ceph version we just installed
        hosts.common.ceph_version(distro.conn)
        distro.conn.exit()


def should_use_custom_repo(args, cd_conf, repo_url):
    """
    A boolean to determine the logic needed to proceed with a custom repo
    installation instead of cramming everything nect to the logic operator.
    """
    if repo_url:
        # repo_url signals a CLI override, return False immediately
        return False
    if cd_conf:
        if cd_conf.has_repos:
            has_valid_release = args.release in cd_conf.get_repos()
            has_default_repo = cd_conf.get_default_repo()
            if has_valid_release or has_default_repo:
                return True
    return False


def custom_repo(distro, args, cd_conf, rlogger, install_ceph=None):
    """
    A custom repo install helper that will go through config checks to retrieve
    repos (and any extra repos defined) and install those

    ``cd_conf`` is the object built from argparse that holds the flags and
    information needed to determine what metadata from the configuration to be
    used.
    """
    default_repo = cd_conf.get_default_repo()
    components = detect_components(args, distro)
    if args.release in cd_conf.get_repos():
        LOG.info('will use repository from conf: %s' % args.release)
        default_repo = args.release
    elif default_repo:
        LOG.info('will use default repository: %s' % default_repo)

    # At this point we know there is a cd_conf and that it has custom
    # repos make sure we were able to detect and actual repo
    if not default_repo:
        LOG.warning('a ceph-deploy config was found with repos \
            but could not default to one')
    else:
        options = dict(cd_conf.items(default_repo))
        options['install_ceph'] = False if install_ceph is False else True
        extra_repos = cd_conf.get_list(default_repo, 'extra-repos')
        rlogger.info('adding custom repository file')
        try:
            distro.repo_install(
                distro,
                default_repo,
                options.pop('baseurl'),
                options.pop('gpgkey'),
                components=components,
                **options
            )
        except KeyError as err:
            raise RuntimeError('missing required key: %s in config section: %s' % (err, default_repo))

        for xrepo in extra_repos:
            rlogger.info('adding extra repo file: %s.repo' % xrepo)
            options = dict(cd_conf.items(xrepo))
            try:
                distro.repo_install(
                    distro,
                    xrepo,
                    options.pop('baseurl'),
                    options.pop('gpgkey'),
                    components=components,
                    **options
                )
            except KeyError as err:
                raise RuntimeError('missing required key: %s in config section: %s' % (err, xrepo))


def install_repo(args):
    """
    For a user that only wants to install the repository only (and avoid
    installing Ceph and its dependencies).
    """
    cd_conf = getattr(args, 'cd_conf', None)

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)
        distro = hosts.get(
            hostname,
            username=args.username,
            # XXX this should get removed once Ceph packages are split for
            # upstream. If default_release is True, it means that the user is
            # trying to install on a RHEL machine and should expect to get RHEL
            # packages. Otherwise, it will need to specify either a specific
            # version, or repo, or a development branch. Other distro users should
            # not see any differences.
            use_rhceph=args.default_release,
        )
        rlogger = logging.getLogger(hostname)

        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        custom_repo(distro, args, cd_conf, rlogger, install_ceph=False)

def remove(args, purge):
    LOG.info('note that some dependencies *will not* be removed because they can cause issues with qemu-kvm')
    LOG.info('like: librbd1 and librados2')
    remove_action = 'Uninstalling'
    if purge:
        remove_action = 'Purging'
    LOG.debug(
        '%s on cluster %s hosts %s',
        remove_action,
        args.cluster,
        ' '.join(args.host),
        )

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)

        distro = hosts.get(
            hostname,
            username=args.username,
            use_rhceph=True)
        LOG.info('Distro info: %s %s %s', distro.name, distro.release, distro.codename)
        rlogger = logging.getLogger(hostname)
        rlogger.info('%s Ceph on %s' % (remove_action, hostname))
        distro.uninstall(distro, purge=purge)
        distro.conn.exit()

def uninstall(args):
    remove(args, False)

def purge(args):
    remove(args, True)

def purgedata(args):
    LOG.debug(
        'Purging data from cluster %s hosts %s',
        args.cluster,
        ' '.join(args.host),
        )

    installed_hosts = []
    for hostname in args.host:
        distro = hosts.get(hostname, username=args.username)
        ceph_is_installed = distro.conn.remote_module.which('ceph')
        if ceph_is_installed:
            installed_hosts.append(hostname)
        distro.conn.exit()

    if installed_hosts:
        LOG.error("Ceph is still installed on: %s", installed_hosts)
        raise RuntimeError("refusing to purge data while Ceph is still installed")

    for hostname in args.host:
        distro = hosts.get(hostname, username=args.username)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        rlogger = logging.getLogger(hostname)
        rlogger.info('purging data on %s' % hostname)

        # Try to remove the contents of /var/lib/ceph first, don't worry
        # about errors here, we deal with them later on
        remoto.process.check(
            distro.conn,
            [
                'rm', '-rf', '--one-file-system', '--', '/var/lib/ceph',
            ]
        )

        # If we failed in the previous call, then we probably have OSDs
        # still mounted, so we unmount them here
        if distro.conn.remote_module.path_exists('/var/lib/ceph'):
            rlogger.warning(
                'OSDs may still be mounted, trying to unmount them'
            )
            remoto.process.run(
                distro.conn,
                [
                    'find', '/var/lib/ceph',
                    '-mindepth', '1',
                    '-maxdepth', '2',
                    '-type', 'd',
                    '-exec', 'umount', '{}', ';',
                ]
            )

            # And now we try again to remove the contents, since OSDs should be
            # unmounted, but this time we do check for errors
            remoto.process.run(
                distro.conn,
                [
                    'rm', '-rf', '--one-file-system', '--', '/var/lib/ceph',
                ]
            )

        remoto.process.run(
            distro.conn,
            [
                'rm', '-rf', '--one-file-system', '--', '/etc/ceph/',
            ]
        )

        distro.conn.exit()


class StoreVersion(argparse.Action):
    """
    Like ``"store"`` but also remember which one of the exclusive
    options was set.

    There are three kinds of versions: stable, testing and dev.
    This sets ``version_kind`` to be the right one of the above.

    This kludge essentially lets us differentiate explicitly set
    values from defaults.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        if self.dest == 'release':
            self.dest = 'stable'
        namespace.version_kind = self.dest


@priority(20)
def make(parser):
    """
    Install Ceph packages on remote hosts.
    """

    version = parser.add_mutually_exclusive_group()

    # XXX deprecated in favor of release
    version.add_argument(
        '--stable',
        nargs='?',
        action=StoreVersion,
        metavar='CODENAME',
        help='[DEPRECATED] install a release known as CODENAME\
                (done by default) (default: %(default)s)',
    )

    version.add_argument(
        '--release',
        nargs='?',
        action=StoreVersion,
        metavar='CODENAME',
        help='install a release known as CODENAME\
                (done by default) (default: %(default)s)',
    )

    version.add_argument(
        '--testing',
        nargs=0,
        action=StoreVersion,
        help='install the latest development release',
    )

    version.add_argument(
        '--dev',
        nargs='?',
        action=StoreVersion,
        const='master',
        metavar='BRANCH_OR_TAG',
        help='install a bleeding edge build from Git branch\
                or tag (default: %(default)s)',
    )
    version.add_argument(
        '--dev-commit',
        nargs='?',
        action=StoreVersion,
        metavar='COMMIT',
        help='install a bleeding edge build from Git commit',
    )

    version.set_defaults(
        stable=None,  # XXX deprecated in favor of release
        release=None,  # Set the default release in sanitize_args()
        dev='master',
        version_kind='stable',
    )

    parser.add_argument(
        '--mon',
        dest='install_mon',
        action='store_true',
        help='install the mon component only',
    )

    parser.add_argument(
        '--mds',
        dest='install_mds',
        action='store_true',
        help='install the mds component only',
    )

    parser.add_argument(
        '--rgw',
        dest='install_rgw',
        action='store_true',
        help='install the rgw component only',
    )

    parser.add_argument(
        '--osd',
        dest='install_osd',
        action='store_true',
        help='install the osd component only',
    )

    parser.add_argument(
        '--tests',
        dest='install_tests',
        action='store_true',
        help='install the testing components',
    )

    parser.add_argument(
        '--cli', '--common',
        dest='install_common',
        action='store_true',
        help='install the common component only',
    )

    parser.add_argument(
        '--all',
        dest='install_all',
        action='store_true',
        help='install all Ceph components (mon, osd, mds, rgw) except tests. This is the default',
    )

    repo = parser.add_mutually_exclusive_group()

    repo.add_argument(
        '--adjust-repos',
        dest='adjust_repos',
        action='store_true',
        help='install packages modifying source repos',
    )

    repo.add_argument(
        '--no-adjust-repos',
        dest='adjust_repos',
        action='store_false',
        help='install packages without modifying source repos',
    )

    repo.add_argument(
        '--repo',
        action='store_true',
        help='install repo files only (skips package installation)',
    )

    repo.set_defaults(
        adjust_repos=True,
    )

    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to install on',
    )

    parser.add_argument(
        '--local-mirror',
        nargs='?',
        const='PATH',
        default=None,
        help='Fetch packages and push them to hosts for a local repo mirror',
    )

    parser.add_argument(
        '--repo-url',
        nargs='?',
        dest='repo_url',
        help='specify a repo URL that mirrors/contains Ceph packages',
    )

    parser.add_argument(
        '--gpg-url',
        nargs='?',
        dest='gpg_url',
        help='specify a GPG key URL to be used with custom repos\
                (defaults to ceph.com)'
    )

    parser.add_argument(
        '--nogpgcheck',
        action='store_true',
        help='install packages without gpgcheck',
    )

    parser.set_defaults(
        func=install,
    )


@priority(80)
def make_uninstall(parser):
    """
    Remove Ceph packages from remote hosts.
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to uninstall Ceph from',
        )
    parser.set_defaults(
        func=uninstall,
        )


@priority(80)
def make_purge(parser):
    """
    Remove Ceph packages from remote hosts and purge all data.
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to purge Ceph from',
        )
    parser.set_defaults(
        func=purge,
        )


@priority(80)
def make_purge_data(parser):
    """
    Purge (delete, destroy, discard, shred) any Ceph data from /var/lib/ceph
    """
    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='hosts to purge Ceph data from',
        )
    parser.set_defaults(
        func=purgedata,
        )
