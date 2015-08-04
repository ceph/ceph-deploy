import pytest

from ceph_deploy.cli import get_parser


class TestParserRepo(object):

    def setup(self):
        self.parser = get_parser()

    def test_repo_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('repo --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy repo' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_repo_name_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('repo'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_repo_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('repo ceph'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_repo_one_host(self):
        args = self.parser.parse_args('repo ceph host1'.split())
        assert args.host == ['host1']

    def test_repo_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['repo', 'ceph'] + hostnames)
        assert frozenset(args.host) == frozenset(hostnames)

    def test_repo_name(self):
        args = self.parser.parse_args('repo ceph host1'.split())
        assert args.repo_name == 'ceph'

    def test_repo_remove_default_is_false(self):
        args = self.parser.parse_args('repo ceph host1'.split())
        assert not args.remove

    def test_repo_remove_set_true(self):
        args = self.parser.parse_args('repo ceph --remove host1'.split())
        assert args.remove

    def test_repo_remove_delete_alias(self):
        args = self.parser.parse_args('repo ceph --delete host1'.split())
        assert args.remove

    def test_repo_url_default_is_none(self):
        args = self.parser.parse_args('repo ceph host1'.split())
        assert args.repo_url is None

    def test_repo_url_custom_path(self):
        args = self.parser.parse_args('repo ceph --repo-url https://ceph.com host1'.split())
        assert args.repo_url == "https://ceph.com"

    def test_repo_gpg_url_default_is_none(self):
        args = self.parser.parse_args('repo ceph host1'.split())
        assert args.gpg_url is None

    def test_repo_gpg_url_custom_path(self):
        args = self.parser.parse_args('repo ceph --gpg-url https://ceph.com/key host1'.split())
        assert args.gpg_url == "https://ceph.com/key"
