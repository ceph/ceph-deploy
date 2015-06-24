import pytest

import ceph_deploy
from ceph_deploy.cli import get_parser


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
        assert err.strip() == ceph_deploy.__version__
