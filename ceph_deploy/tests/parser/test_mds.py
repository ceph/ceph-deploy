import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


class TestParserMDS(object):

    def setup(self):
        self.parser = get_parser()

    def test_mds_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mds --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy mds' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_mds_create_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('mds create'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_mds_create_one_host(self):
        args = self.parser.parse_args('mds create host1'.split())
        assert args.mds[0][0] == 'host1'

    def test_mds_create_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['mds', 'create'] + hostnames)
        # args.mds is a list of tuples, and tuple[0] is the hostname
        hosts = [x[0] for x in args.mds]
        assert frozenset(hosts) == frozenset(hostnames)
