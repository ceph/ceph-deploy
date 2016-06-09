import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments

SUBCMDS_WITH_ARGS = ['list', 'create', 'prepare', 'activate']


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
        assert args.disk[0][0] == 'host1'

    def test_osd_list_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('osd list'.split() + hostnames)
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames

    def test_osd_create_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd create --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy osd create' in out

    def test_osd_create_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd create'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_osd_create_single_host(self):
        args = self.parser.parse_args('osd create host1:sdb'.split())
        assert args.disk[0][0] == 'host1'

    def test_osd_create_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('osd create'.split() + [x + ":sdb" for x in hostnames])
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames

    def test_osd_create_zap_default_false(self):
        args = self.parser.parse_args('osd create host1:sdb'.split())
        assert args.zap_disk is False

    def test_osd_create_zap_true(self):
        args = self.parser.parse_args('osd create --zap-disk host1:sdb'.split())
        assert args.zap_disk is True

    def test_osd_create_fstype_default_xfs(self):
        args = self.parser.parse_args('osd create host1:sdb'.split())
        assert args.fs_type == "xfs"

    def test_osd_create_fstype_btrfs(self):
        args = self.parser.parse_args('osd create --fs-type btrfs host1:sdb'.split())
        assert args.fs_type == "btrfs"

    def test_osd_create_fstype_invalid(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd create --fs-type bork host1:sdb'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_osd_create_dmcrypt_default_false(self):
        args = self.parser.parse_args('osd create host1:sdb'.split())
        assert args.dmcrypt is False

    def test_osd_create_dmcrypt_true(self):
        args = self.parser.parse_args('osd create --dmcrypt host1:sdb'.split())
        assert args.dmcrypt is True

    def test_osd_create_dmcrypt_key_dir_default(self):
        args = self.parser.parse_args('osd create host1:sdb'.split())
        assert args.dmcrypt_key_dir == "/etc/ceph/dmcrypt-keys"

    def test_osd_create_dmcrypt_key_dir_custom(self):
        args = self.parser.parse_args('osd create --dmcrypt --dmcrypt-key-dir /tmp/keys host1:sdb'.split())
        assert args.dmcrypt_key_dir == "/tmp/keys"

    def test_osd_prepare_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd prepare --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy osd prepare' in out

    def test_osd_prepare_zap_default_false(self):
        args = self.parser.parse_args('osd prepare host1:sdb'.split())
        assert args.zap_disk is False

    def test_osd_prepare_zap_true(self):
        args = self.parser.parse_args('osd prepare --zap-disk host1:sdb'.split())
        assert args.zap_disk is True

    def test_osd_prepare_fstype_default_xfs(self):
        args = self.parser.parse_args('osd prepare host1:sdb'.split())
        assert args.fs_type == "xfs"

    def test_osd_prepare_fstype_invalid(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd prepare --fs-type bork host1:sdb'.split())
        out, err = capsys.readouterr()
        assert 'invalid choice' in err

    def test_osd_prepare_dmcrypt_default_false(self):
        args = self.parser.parse_args('osd prepare host1:sdb'.split())
        assert args.dmcrypt is False

    def test_osd_prepare_dmcrypt_true(self):
        args = self.parser.parse_args('osd prepare --dmcrypt host1:sdb'.split())
        assert args.dmcrypt is True

    def test_osd_prepare_dmcrypt_key_dir_default(self):
        args = self.parser.parse_args('osd prepare host1:sdb'.split())
        assert args.dmcrypt_key_dir == "/etc/ceph/dmcrypt-keys"

    def test_osd_prepare_dmcrypt_key_dir_custom(self):
        args = self.parser.parse_args('osd prepare --dmcrypt --dmcrypt-key-dir /tmp/keys host1:sdb'.split())
        assert args.dmcrypt_key_dir == "/tmp/keys"

    def test_osd_prepare_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd prepare'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_osd_prepare_single_host(self):
        args = self.parser.parse_args('osd prepare host1:sdb'.split())
        assert args.disk[0][0] == 'host1'

    def test_osd_prepare_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('osd prepare'.split() + [x + ":sdb" for x in hostnames])
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames

    def test_osd_activate_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd activate --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy osd activate' in out

    def test_osd_activate_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('osd activate'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_osd_activate_single_host(self):
        args = self.parser.parse_args('osd activate host1:sdb1'.split())
        assert args.disk[0][0] == 'host1'

    def test_osd_activate_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('osd activate'.split() + [x + ":sdb1" for x in hostnames])
        # args.disk is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.disk]
        assert hosts == hostnames
