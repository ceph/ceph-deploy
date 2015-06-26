import pytest
from mock import patch

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.fakes import fake_arg_val_hostname

@patch('ceph_deploy.util.arg_validators.Hostname.__call__', fake_arg_val_hostname)
class TestParserNew(object):

    def setup(self):
        self.parser = get_parser()

    def test_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('new --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy new' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_new_copykey_true_by_default(self):
        args = self.parser.parse_args('new host1'.split())
        assert args.ssh_copykey

    def test_new_copykey_false(self):
        args = self.parser.parse_args('new --no-ssh-copykey host1'.split())
        assert not args.ssh_copykey

    def test_new_fsid_none_by_default(self):
        args = self.parser.parse_args('new host1'.split())
        assert args.fsid is None

    def test_new_fsid_custom_fsid(self):
        args = self.parser.parse_args('new --fsid bc50d015-65c9-457a-bfed-e37b92756527 host1'.split())
        assert args.fsid == 'bc50d015-65c9-457a-bfed-e37b92756527'

    @pytest.mark.skipif(reason="no UUID validation yet")
    def test_new_fsid_custom_fsid_bad(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('new --fsid bc50d015-65c9-457a-bfed-e37'.split())
        out, err = capsys.readouterr()
        #TODO check for correct error string in err

    def test_new_networks_none_by_default(self):
        args = self.parser.parse_args('new host1'.split())
        assert args.public_network is None
        assert args.cluster_network is None

    def test_new_public_network_custom(self):
        args = self.parser.parse_args('new --public-network 10.10.0.0/16 host1'.split())
        assert args.public_network == "10.10.0.0/16"

    def test_new_cluster_network_custom(self):
        args = self.parser.parse_args('new --cluster-network 10.10.0.0/16 host1'.split())
        assert args.cluster_network == "10.10.0.0/16"

    def test_new_public_network_custom_bad(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('new --public-network 10.10.0.0'.split())
        out, err = capsys.readouterr()
        assert "error: subnet must" in err

    def test_new_cluster_network_custom_bad(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('new --cluster-network 10.10.0.0'.split())
        out, err = capsys.readouterr()
        assert "error: subnet must" in err

    def test_new_mon_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('new'.split())
        out, err = capsys.readouterr()
        assert "error: too few arguments" in err

    def test_new_one_mon(self):
        hostnames = ['test1']
        args = self.parser.parse_args(['new'] + hostnames)
        assert args.mon == hostnames

    def test_new_multiple_mons(self):
        hostnames = ['test1', 'test2', 'test3']
        args = self.parser.parse_args(['new'] + hostnames)
        assert frozenset(args.mon) == frozenset(hostnames)
