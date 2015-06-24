import pytest

from ceph_deploy.cli import get_parser


class TestParserInstall(object):

    def setup(self):
        self.parser = get_parser()

    def test_install_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('install --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy install' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_install_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('install'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_install_one_host(self):
        args = self.parser.parse_args('install host1'.split())
        assert args.host == ['host1']

    def test_install_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['install'] + hostnames)
        assert frozenset(args.host) == frozenset(hostnames)

    def test_install_release_default_is_none(self):
        args = self.parser.parse_args('install host1'.split())
        assert args.release is None
        assert args.version_kind == "stable"

    def test_install_release(self):
        args = self.parser.parse_args('install --release hammer host1'.split())
        assert args.release == "hammer"
        assert args.version_kind == "stable"

    @pytest.mark.skipif(reason="No release name sanity checking yet")
    def test_install_release_bad_codename(self):
        args = self.parser.parse_args('install --release cephalopod host1'.split())
        assert args.release != "cephalopod"

    def test_install_testing_default_is_none(self):
        args = self.parser.parse_args('install host1'.split())
        assert args.testing is None
        assert args.version_kind == "stable"

    def test_install_testing_true(self):
        args = self.parser.parse_args('install --testing host1'.split())
        assert len(args.testing) == 0
        assert args.version_kind == "testing"

    def test_install_dev_disabled_by_default(self):
        args = self.parser.parse_args('install host1'.split())
        # dev defaults to master, but version_kind nullifies it
        assert args.dev == "master"
        assert args.version_kind == "stable"

    def test_install_dev_custom_version(self):
        args = self.parser.parse_args('install --dev v0.80.8 host1'.split())
        assert args.dev == "v0.80.8"
        assert args.version_kind == "dev"

    @pytest.mark.skipif(reason="test reflects desire, but not code reality")
    def test_install_dev_option_default_is_master(self):
        # I don't think this is the way argparse works.
        args = self.parser.parse_args('install --dev host1'.split())
        assert args.dev == "master"
        assert args.version_kind == "dev"

    def test_install_release_testing_mutex(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('install --release hammer --testing host1'.split())
        out, err = capsys.readouterr()
        assert 'not allowed with argument' in err

    def test_install_release_dev_mutex(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('install --release hammer --dev master host1'.split())
        out, err = capsys.readouterr()
        assert 'not allowed with argument' in err

    def test_install_testing_dev_mutex(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('install --testing --dev master host1'.split())
        out, err = capsys.readouterr()
        assert 'not allowed with argument' in err
