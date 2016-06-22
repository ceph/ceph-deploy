import pytest

import ceph_deploy
from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


SUBCMDS_WITH_ARGS = [
    'new', 'install', 'rgw', 'mds', 'mon', 'gatherkeys', 'disk', 'osd',
    'admin', 'config', 'uninstall', 'purgedata', 'purge', 'pkg', 'calamari'
]
SUBCMDS_WITHOUT_ARGS = ['forgetkeys']


class TestParserMain(object):

    def setup(self):
        self.parser = get_parser()

    def test_verbose_true(self):
        args = self.parser.parse_args('--verbose forgetkeys'.split())
        assert args.verbose

    def test_verbose_default_is_false(self):
        args = self.parser.parse_args('forgetkeys'.split())
        assert not args.verbose

    def test_quiet_true(self):
        args = self.parser.parse_args('--quiet forgetkeys'.split())
        assert args.quiet

    def test_quiet_default_is_false(self):
        args = self.parser.parse_args('forgetkeys'.split())
        assert not args.quiet

    def test_verbose_quiet_are_mutually_exclusive(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('--verbose --quiet forgetkeys'.split())
        out, err = capsys.readouterr()
        assert 'not allowed with argument' in err

    def test_version(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('--version'.split())
        out, err = capsys.readouterr()
        assert ceph_deploy.__version__ in (out.strip(), err.strip())

    def test_custom_username(self):
        args = self.parser.parse_args('--username trhoden forgetkeys'.split())
        assert args.username == 'trhoden'

    def test_default_username_is_none(self):
        args = self.parser.parse_args('forgetkeys'.split())
        assert args.username is None

    def test_overwrite_conf_default_false(self):
        args = self.parser.parse_args('forgetkeys'.split())
        assert not args.overwrite_conf

    def test_overwrite_conf_true(self):
        args = self.parser.parse_args('--overwrite-conf forgetkeys'.split())
        assert args.overwrite_conf

    def test_default_cluster_name(self):
        args = self.parser.parse_args('forgetkeys'.split())
        assert args.cluster == 'ceph'

    def test_custom_cluster_name(self):
        args = self.parser.parse_args('--cluster myhugecluster forgetkeys'.split())
        assert args.cluster == 'myhugecluster'

    def test_custom_cluster_name_bad(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('--cluster=/evil-this-should-not-be-created'.split())
        out, err = capsys.readouterr()
        assert ('--cluster: argument must start with a letter and contain only '
                'letters and numbers') in err

    def test_default_ceph_conf_is_none(self):
        args = self.parser.parse_args('forgetkeys'.split())
        assert args.ceph_conf is None

    def test_custom_ceph_conf(self):
        args = self.parser.parse_args('--ceph-conf /tmp/ceph.conf forgetkeys'.split())
        assert args.ceph_conf == '/tmp/ceph.conf'

    @pytest.mark.parametrize('cmd', SUBCMDS_WITH_ARGS)
    def test_valid_subcommands_with_args(self, cmd, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args(['%s' % cmd])
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)
        assert 'invalid choice' not in err

    @pytest.mark.parametrize('cmd', SUBCMDS_WITHOUT_ARGS)
    def test_valid_subcommands_without_args(self, cmd, capsys):
        self.parser.parse_args(['%s' % cmd])

    def test_invalid_subcommand(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('bork'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('--help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy' in out
        assert 'optional arguments:' in out
        assert 'commands:' in out
