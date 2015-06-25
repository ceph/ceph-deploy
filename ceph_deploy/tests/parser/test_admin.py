import pytest

from ceph_deploy.cli import get_parser


class TestParserAdmin(object):

    def setup(self):
        self.parser = get_parser()

    def test_admin_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('admin --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy admin' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_admin_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('admin'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_admin_one_host(self):
        args = self.parser.parse_args('admin host1'.split())
        assert args.client == ['host1']

    def test_admin_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['admin'] + hostnames)
        assert args.client == hostnames
