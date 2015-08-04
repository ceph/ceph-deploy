import os
import logging

from ceph_deploy import hosts
from ceph_deploy.cliutil import priority


LOG = logging.getLogger(__name__)


def install_repo(distro, args, cd_conf, rlogger):
    if args.repo_name in cd_conf.get_repos():
        LOG.info('will use repository %s from ceph-deploy config', args.repo_name)
        options = dict(cd_conf.items(args.repo_name))
        extra_repos = cd_conf.get_list(args.repo_name, 'extra-repos')
        try:
            repo_url = options.pop('baseurl')
            gpg_url = options.pop('gpgkey', None)
        except KeyError as err:
            raise RuntimeError(
                'missing required key: %s in config section: %s' % (err, args.repo_name)
            )
    else:
        repo_url = os.environ.get('CEPH_DEPLOY_REPO_URL') or args.repo_url
        gpg_url = os.environ.get('CEPH_DEPLOY_GPG_URL') or args.gpg_url
        extra_repos = []

    repo_url = repo_url.strip('/')  # Remove trailing slashes
    distro.packager.add_repo(
        args.repo_name,
        repo_url,
        gpg_url=gpg_url
    )

    for xrepo in extra_repos:
        rlogger.info('adding extra repo: %s' % xrepo)
        options = dict(cd_conf.items(xrepo))
        try:
            repo_url = options.pop('baseurl')
            gpg_url = options.pop('gpgkey', None)
        except KeyError as err:
            raise RuntimeError(
                'missing required key: %s in config section: %s' % (err, xrepo)
            )
        distro.packager.add_repo(
            args.repo_name,
            repo_url,
            gpg_url=gpg_url
        )


def repo(args):
    cd_conf = getattr(args, 'cd_conf', None)

    for hostname in args.host:
        LOG.debug('Detecting platform for host %s ...', hostname)
        distro = hosts.get(
            hostname,
            username=args.username
        )
        rlogger = logging.getLogger(hostname)

        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )

        if args.remove:
            distro.packager.remove_repo(args.repo_name)
        else:
            install_repo(distro, args, cd_conf, rlogger)


@priority(70)
def make(parser):
    """
    Repo definition management
    """

    parser.add_argument(
        'repo_name',
        metavar='REPO-NAME',
        help='Name of repo to manage.  Can match an entry in cephdeploy.conf'
    )

    parser.add_argument(
        '--repo-url',
        help='a repo URL that mirrors/contains Ceph packages'
    )

    parser.add_argument(
        '--gpg-url',
        help='a GPG key URL to be used with custom repos'
    )

    parser.add_argument(
        '--remove', '--delete',
        action='store_true',
        help='remove repo definition on remote host'
    )

    parser.add_argument(
        'host',
        metavar='HOST',
        nargs='+',
        help='host(s) to install on'
    )

    parser.set_defaults(
        func=repo
    )
