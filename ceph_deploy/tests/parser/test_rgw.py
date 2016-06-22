import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


class TestParserRGW(object):

    def setup(self):
        self.parser = get_parser()

    def test_rgw_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('rgw --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy rgw' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_rgw_create_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('rgw create'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_rgw_create_one_host(self):
        args = self.parser.parse_args('rgw create host1'.split())
        assert args.rgw[0][0] == 'host1'

    def test_rgw_create_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['rgw', 'create'] + hostnames)
        # args.rgw is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.rgw]
        assert frozenset(hosts) == frozenset(hostnames)
