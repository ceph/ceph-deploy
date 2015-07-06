import pytest

from ceph_deploy.cli import get_parser

SUBCMDS_WITH_ARGS = ['add', 'destroy', 'create']
SUBCMDS_WITHOUT_ARGS = ['create', 'create-initial']


class TestParserMON(object):

    def setup(self):
        self.parser = get_parser()

    def test_mon_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy mon' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    @pytest.mark.parametrize('cmd', SUBCMDS_WITH_ARGS)
    def test_mon_valid_subcommands_with_args(self, cmd, capsys):
        args = self.parser.parse_args(['mon'] + ['%s' % cmd] + ['host1'])
        assert args.subcommand == cmd

    @pytest.mark.parametrize('cmd', SUBCMDS_WITHOUT_ARGS)
    def test_mon_valid_subcommands_without_args(self, cmd, capsys):
        args = self.parser.parse_args(['mon'] + ['%s' % cmd])
        assert args.subcommand == cmd

    def test_mon_invalid_subcommand(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon bork'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_mon_create_initial_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon create-initial --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy mon create-initial' in out

    def test_mon_create_initial_keyrings_default_none(self):
        args = self.parser.parse_args('mon create-initial'.split())
        assert args.keyrings is None

    def test_mon_create_initial_keyrings_custom_dir(self):
        args = self.parser.parse_args('mon create-initial --keyrings /tmp/keys'.split())
        assert args.keyrings == "/tmp/keys"

    def test_mon_create_initial_keyrings_host_raises_err(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon create-initial test1'.split())

    def test_mon_create_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon create --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy mon create' in out

    def test_mon_create_keyrings_default_none(self):
        args = self.parser.parse_args('mon create'.split())
        assert args.keyrings is None

    def test_mon_create_keyrings_custom_dir(self):
        args = self.parser.parse_args('mon create --keyrings /tmp/keys'.split())
        assert args.keyrings == "/tmp/keys"

    def test_mon_create_single_host(self):
        args = self.parser.parse_args('mon create test1'.split())
        assert args.mon == ['test1']

    def test_mon_create_multi_host(self):
        hosts = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('mon create'.split() + hosts)
        assert args.mon == hosts

    def test_mon_add_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon add --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy mon add' in out

    def test_mon_add_address_default_none(self):
        args = self.parser.parse_args('mon add test1'.split())
        assert args.address is None

    def test_mon_add_address_custom_addr(self):
        args = self.parser.parse_args('mon add test1 --address 10.10.0.1'.split())
        assert args.address == '10.10.0.1'

    def test_mon_add_no_host_raises_err(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon add'.split())

    def test_mon_add_one_host_okay(self):
        args = self.parser.parse_args('mon add test1'.split())
        assert args.mon == ["test1"]

    def test_mon_add_multi_host_raises_err(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon add test1 test2'.split())

    def test_mon_destroy_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon destroy --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy mon destroy' in out

    def test_mon_destroy_no_host_raises_err(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon destroy'.split())

    def test_mon_destroy_one_host_okay(self):
        args = self.parser.parse_args('mon destroy test1'.split())
        assert args.mon == ["test1"]

    def test_mon_destroy_multi_host(self):
        hosts = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('mon destroy'.split() + hosts)
        assert args.mon == hosts
