import pytest

from ceph_deploy.cli import get_parser


class TestParserUninstall(object):

    def setup(self):
        self.parser = get_parser()

    def test_uninstall_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('uninstall --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy uninstall' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_uninstall_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('uninstall'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_uninstall_one_host(self):
        args = self.parser.parse_args('uninstall host1'.split())
        assert args.host == ['host1']

    def test_uninstall_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['uninstall'] + hostnames)
        assert frozenset(args.host) == frozenset(hostnames)
