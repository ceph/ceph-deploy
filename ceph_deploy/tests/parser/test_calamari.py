import pytest

from ceph_deploy.cli import get_parser


class TestParserCalamari(object):

    def setup(self):
        self.parser = get_parser()

    def test_calamari_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('calamari --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy calamari' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_calamari_connect_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('calamari connect --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy calamari connect' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_calamari_connect_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('calamari connect'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_calamari_connect_one_host(self):
        args = self.parser.parse_args('calamari connect host1'.split())
        assert args.hosts == ['host1']

    def test_calamari_connect_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('calamari connect'.split() + hostnames)
        assert args.hosts == hostnames

    def test_calamari_connect_master_default_is_none(self):
        args = self.parser.parse_args('calamari connect host1'.split())
        assert args.master is None

    def test_calamari_connect_master_custom(self):
        args = self.parser.parse_args('calamari connect --master master.ceph.com host1'.split())
        assert args.master == "master.ceph.com"
