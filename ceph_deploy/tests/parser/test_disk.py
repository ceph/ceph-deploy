import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments

SUBCMDS_WITH_ARGS = ['list', 'zap']


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
        assert_too_few_arguments(err)

    def test_disk_list_single_host(self):
        args = self.parser.parse_args('disk list host1'.split())
        assert args.host[0] == 'host1'
        assert args.debug is False

    def test_disk_list_single_host_debug(self):
        args = self.parser.parse_args('disk list --debug host1'.split())
        assert args.host[0] == 'host1'
        assert args.debug is True

    def test_disk_list_multi_host(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args('disk list'.split() + hostnames)
        assert args.host == hostnames

    def test_disk_zap_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk zap --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy disk zap' in out

    def test_disk_zap_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('disk zap'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_disk_zap_single_host(self):
        args = self.parser.parse_args('disk zap host1 /dev/sdb'.split())
        assert args.disk[0] == '/dev/sdb'
        assert args.host == 'host1'
        assert args.debug is False

    def test_disk_zap_multi_host(self):
        host = 'host1'
        disks = ['/dev/sda1', '/dev/sda2']
        args = self.parser.parse_args(['disk', 'zap', host] + disks)
        assert args.disk == disks

    def test_disk_zap_debug_true(self):
        args = \
            self.parser.parse_args('disk zap --debug host1 /dev/sdb'.split())
        assert args.disk[0] == '/dev/sdb'
        assert args.host == 'host1'
        assert args.debug is True
