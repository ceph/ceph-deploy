import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


class TestParserPurge(object):

    def setup(self):
        self.parser = get_parser()

    def test_purge_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('purge --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy purge' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_purge_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('purge'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_purge_one_host(self):
        args = self.parser.parse_args('purge host1'.split())
        assert args.host == ['host1']

    def test_purge_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['purge'] + hostnames)
        assert frozenset(args.host) == frozenset(hostnames)
