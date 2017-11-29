import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments

SUBCMDS_WITH_ARGS = ['list', 'create']


class TestParserOSD(object):

    def setup(self):
        self.parser = get_parser()

    def test_osd_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy osd' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    @pytest.mark.parametrize('cmd', SUBCMDS_WITH_ARGS)
    def test_osd_valid_subcommands_with_args(self, cmd):
        self.parser.parse_args(['osd'] + ['%s' % cmd] + ['host1'])

    def test_osd_invalid_subcommand(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd bork'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_osd_list_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd list --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy osd list' in out

    def test_osd_list_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd list'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_osd_list_single_host(self):
        args = self.parser.parse_args('osd list host1'.split())
        assert args.host[0] == 'host1'

    def test_osd_list_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('osd list'.split() + hostnames)
        assert args.host == hostnames

    def test_osd_create_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd create --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy osd create' in out

    def test_osd_create_single_host(self):
        args = self.parser.parse_args('osd create host1 --data /dev/sdb'.split())
        assert args.host == 'host1'
        assert args.data == '/dev/sdb'

    def test_osd_create_zap_default_false(self):
        args = self.parser.parse_args('osd create host1 --data /dev/sdb'.split())
        assert args.zap_disk is False

    def test_osd_create_zap_true(self):
        args = self.parser.parse_args('osd create --zap-disk host1 --data /dev/sdb'.split())
        assert args.zap_disk is True

    def test_osd_create_fstype_default_xfs(self):
        args = self.parser.parse_args('osd create host1 --data /dev/sdb'.split())
        assert args.fs_type == "xfs"

    def test_osd_create_fstype_btrfs(self):
        args = self.parser.parse_args('osd create --fs-type btrfs host1 --data /dev/sdb'.split())
        assert args.fs_type == "btrfs"

    def test_osd_create_fstype_invalid(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd create --fs-type bork host1 --data /dev/sdb'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_osd_create_dmcrypt_default_false(self):
        args = self.parser.parse_args('osd create host1 --data /dev/sdb'.split())
        assert args.dmcrypt is False

    def test_osd_create_dmcrypt_true(self):
        args = self.parser.parse_args('osd create --dmcrypt host1 --data /dev/sdb'.split())
        assert args.dmcrypt is True

    def test_osd_create_dmcrypt_key_dir_default(self):
        args = self.parser.parse_args('osd create host1 --data /dev/sdb'.split())
        assert args.dmcrypt_key_dir == "/etc/ceph/dmcrypt-keys"

    def test_osd_create_dmcrypt_key_dir_custom(self):
        args = self.parser.parse_args('osd create --dmcrypt --dmcrypt-key-dir /tmp/keys host1 --data /dev/sdb'.split())
        assert args.dmcrypt_key_dir == "/tmp/keys"

