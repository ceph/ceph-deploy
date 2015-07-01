import pytest

from ceph_deploy.cli import get_parser

SUBCMDS_WITH_ARGS = ['push', 'pull']


class TestParserConfig(object):

    def setup(self):
        self.parser = get_parser()

    def test_config_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('config --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy config' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    @pytest.mark.parametrize('cmd', SUBCMDS_WITH_ARGS)
    def test_config_subcommands_with_args(self, cmd):
        self.parser.parse_args(['config'] + ['%s' % cmd] + ['host1'])

    def test_config_invalid_subcommand(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('config bork'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_config_push_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('config push'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_config_push_one_host(self):
        args = self.parser.parse_args('config push host1'.split())
        assert args.client == ['host1']

    def test_config_push_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('config push'.split() + hostnames)
        assert args.client == hostnames

    def test_config_pull_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('config pull'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_config_pull_one_host(self):
        args = self.parser.parse_args('config pull host1'.split())
        assert args.client == ['host1']

    def test_config_pull_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('config pull'.split() + hostnames)
        assert args.client == hostnames
