import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


class TestParserPurgeData(object):

    def setup(self):
        self.parser = get_parser()

    def test_purgedata_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('purgedata --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy purgedata' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_purgedata_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('purgedata'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_purgedata_one_host(self):
        args = self.parser.parse_args('purgedata host1'.split())
        assert args.host == ['host1']

    def test_purgedata_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['purgedata'] + hostnames)
        assert frozenset(args.host) == frozenset(hostnames)
