import logging

from ceph_deploy.cliutil import priority


LOG = logging.getLogger(__name__)


def repo(args):
    pass


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
