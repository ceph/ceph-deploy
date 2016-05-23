import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


class TestParserPkg(object):

    def setup(self):
        self.parser = get_parser()

    def test_pkg_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('pkg --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy pkg' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_pkg_install_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('pkg --install pkg1'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_pkg_install_one_host(self):
        args = self.parser.parse_args('pkg --install pkg1 host1'.split())
        assert args.hosts == ['host1']
        assert args.install == "pkg1"

    def test_pkg_install_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('pkg --install pkg1'.split() + hostnames)
        assert args.hosts == hostnames
        assert args.install == "pkg1"

    def test_pkg_install_muliple_pkgs(self):
        args = self.parser.parse_args('pkg --install pkg1,pkg2 host1'.split())
        assert args.install == "pkg1,pkg2"

    def test_pkg_remove_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('pkg --remove pkg1'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_pkg_remove_one_host(self):
        args = self.parser.parse_args('pkg --remove pkg1 host1'.split())
        assert args.hosts == ['host1']
        assert args.remove == "pkg1"

    def test_pkg_remove_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('pkg --remove pkg1'.split() + hostnames)
        assert args.hosts == hostnames
        assert args.remove == "pkg1"

    def test_pkg_remove_muliple_pkgs(self):
        args = self.parser.parse_args('pkg --remove pkg1,pkg2 host1'.split())
        assert args.remove == "pkg1,pkg2"

    def test_pkg_install_remove_are_mutex(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('pkg --install pkg2 --remove pkg1 host1'.split())
        out, err = capsys.readouterr()
        assert "argument --remove: not allowed with argument --install" in err
