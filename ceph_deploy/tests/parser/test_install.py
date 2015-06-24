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

    def test_install_release(self):
        args = self.parser.parse_args('install --release hammer host1'.split())
        assert args.release == "hammer"
        assert args.version_kind == "stable"

    @pytest.mark.skipif(reason="No release name sanity checking yet")
    def test_install_release_bad_codename(self):
        args = self.parser.parse_args('install --release cephalopod host1'.split())
        assert args.release != "cephalopod"
        
