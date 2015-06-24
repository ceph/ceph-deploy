import pytest

from ceph_deploy.cli import get_parser

SUBCMDS_WITH_ARGS = ['add', 'destroy']
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

    @pytest.mark.skipif(reason="http://tracker.ceph.com/issues/12150")
    @pytest.mark.parametrize('cmd', SUBCMDS_WITH_ARGS)
    def test_mon_valid_subcommands_with_args(self, cmd, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args(['mon'] + ['%s' % cmd] + ['host1'])
        out, err = capsys.readouterr()
        assert 'too few arguments' in err
        assert 'invalid choice' not in err

    @pytest.mark.parametrize('cmd', SUBCMDS_WITHOUT_ARGS)
    def test_mon_valid_subcommands_without_args(self, cmd, capsys):
        self.parser.parse_args(['mon'] + ['%s' % cmd])

    def test_mon_invalid_subcommand(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon bork'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    @pytest.mark.skipif(reason="http://tracker.ceph.com/issues/12151")
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

    @pytest.mark.skipif(reason="http://tracker.ceph.com/issues/12151")
    def test_mon_create_initial_keyrings_host_raises_err(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mon create-initial test1'.split())

    @pytest.mark.skipif(reason="http://tracker.ceph.com/issues/12151")
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
