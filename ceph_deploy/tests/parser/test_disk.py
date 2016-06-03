import pytest

from ceph_deploy.cli import get_parser

SUBCMDS_WITH_ARGS = ['list', 'prepare', 'activate', 'zap']


class TestParserDisk(object):

    def setup(self):
        self.parser = get_parser()

    def test_disk_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy disk' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    @pytest.mark.parametrize('cmd', SUBCMDS_WITH_ARGS)
    def test_disk_valid_subcommands_with_args(self, cmd):
        self.parser.parse_args(['disk'] + ['%s' % cmd] + ['host1'])

    def test_disk_invalid_subcommand(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk bork'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_disk_list_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk list --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy disk list' in out

    def test_disk_list_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk list'.split())
        out, err = capsys.readouterr()
        assert 'too few arguments' in err

    def test_disk_list_single_host(self):
        args = self.parser.parse_args('disk list host1'.split())
        assert args.disk[0][0] == 'host1'

    def test_disk_list_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('disk list'.split() + hostnames)
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames

    def test_disk_prepare_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk prepare --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy disk prepare' in out

    def test_disk_prepare_zap_default_false(self):
        args = self.parser.parse_args('disk prepare host1:sdb'.split())
        assert args.zap_disk is False

    def test_disk_prepare_zap_true(self):
        args = self.parser.parse_args('disk prepare --zap-disk host1:sdb'.split())
        assert args.zap_disk is True

    def test_disk_prepare_fstype_default_xfs(self):
        args = self.parser.parse_args('disk prepare host1:sdb'.split())
        assert args.fs_type == "xfs"

    def test_disk_prepare_fstype_btrfs(self):
        args = self.parser.parse_args('disk prepare --fs-type btrfs host1:sdb'.split())
        assert args.fs_type == "btrfs"

    def test_disk_prepare_fstype_invalid(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk prepare --fs-type bork host1:sdb'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_disk_prepare_dmcrypt_default_false(self):
        args = self.parser.parse_args('disk prepare host1:sdb'.split())
        assert args.dmcrypt is False

    def test_disk_prepare_dmcrypt_true(self):
        args = self.parser.parse_args('disk prepare --dmcrypt host1:sdb'.split())
        assert args.dmcrypt is True

    def test_disk_prepare_dmcrypt_key_dir_default(self):
        args = self.parser.parse_args('disk prepare host1:sdb'.split())
        assert args.dmcrypt_key_dir == "/etc/ceph/dmcrypt-keys"

    def test_disk_prepare_dmcrypt_key_dir_custom(self):
        args = self.parser.parse_args('disk prepare --dmcrypt --dmcrypt-key-dir /tmp/keys host1:sdb'.split())
        assert args.dmcrypt_key_dir == "/tmp/keys"

    def test_disk_prepare_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk prepare'.split())
        out, err = capsys.readouterr()
        assert 'too few arguments' in err

    def test_disk_prepare_single_host(self):
        args = self.parser.parse_args('disk prepare host1:sdb'.split())
        assert args.disk[0][0] == 'host1'

    def test_disk_prepare_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('disk prepare'.split() + [x + ":sdb" for x in hostnames])
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames

    def test_disk_activate_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk activate --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy disk activate' in out

    def test_disk_activate_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk activate'.split())
        out, err = capsys.readouterr()
        assert 'too few arguments' in err

    def test_disk_activate_single_host(self):
        args = self.parser.parse_args('disk activate host1:sdb1'.split())
        assert args.disk[0][0] == 'host1'

    def test_disk_activate_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('disk activate'.split() + [x + ":sdb1" for x in hostnames])
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames

    def test_disk_zap_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk zap --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy disk zap' in out

    def test_disk_zap_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk zap'.split())
        out, err = capsys.readouterr()
        assert 'too few arguments' in err

    def test_disk_zap_single_host(self):
        args = self.parser.parse_args('disk zap host1:sdb'.split())
        assert args.disk[0][0] == 'host1'

    def test_disk_zap_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('disk zap'.split() + [x + ":sdb" for x in hostnames])
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames
