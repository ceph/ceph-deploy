import pytest

from ceph_deploy.cli import get_parser
from ceph_deploy.tests.util import assert_too_few_arguments


class TestParserGatherKeys(object):

    def setup(self):
        self.parser = get_parser()

    def test_gather_help(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('gatherkeys --help'.split())
        out, err = capsys.readouterr()
        assert 'usage: ceph-deploy gatherkeys' in out
        assert 'positional arguments:' in out
        assert 'optional arguments:' in out

    def test_gatherkeys_host_required(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args('gatherkeys'.split())
        out, err = capsys.readouterr()
        assert_too_few_arguments(err)

    def test_gatherkeys_one_host(self):
        args = self.parser.parse_args('gatherkeys host1'.split())
        assert args.mon == ['host1']

    def test_gatherkeys_multiple_hosts(self):
        hostnames = ['host1', 'host2', 'host3']
        args = self.parser.parse_args(['gatherkeys'] + hostnames)
        assert args.mon == hostnames
