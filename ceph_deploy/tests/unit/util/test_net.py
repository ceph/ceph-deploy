try:
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import HTTPError

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from ceph_deploy.util import net
from ceph_deploy.tests import util
import pytest


# The following class adds about 1900 tests via py.test generation

class TestIpInSubnet(object):

    @pytest.mark.parametrize('ip', util.generate_ips("10.0.0.1", "10.0.0.255"))
    def test_correct_for_10_0_0_255(self, ip):
        assert net.ip_in_subnet(ip, "10.0.0.0/16")

    @pytest.mark.parametrize('ip', util.generate_ips("10.0.0.1", "10.0.0.255"))
    def test_false_for_10_0_0_255(self, ip):
        assert net.ip_in_subnet(ip, "10.2.0.0/24") is False

    @pytest.mark.parametrize('ip', util.generate_ips("255.255.255.1", "255.255.255.255"))
    def test_false_for_255_addresses(self, ip):
        assert net.ip_in_subnet(ip, "10.9.1.0/16") is False

    @pytest.mark.parametrize('ip', util.generate_ips("172.7.1.1", "172.7.1.255"))
    def test_false_for_172_addresses(self, ip):
        assert net.ip_in_subnet(ip, "172.3.0.0/16") is False

    @pytest.mark.parametrize('ip', util.generate_ips("10.9.8.0", "10.9.8.255"))
    def test_true_for_16_subnets(self, ip):
        assert net.ip_in_subnet(ip, "10.9.1.0/16") is True

    @pytest.mark.parametrize('ip', util.generate_ips("10.9.8.0", "10.9.8.255"))
    def test_false_for_24_subnets(self, ip):
        assert net.ip_in_subnet(ip, "10.9.1.0/24") is False


class TestGetRequest(object):

    def test_urlopen_fails(self, monkeypatch):
        def bad_urlopen(url):
            raise HTTPError('url', 500, 'error', '', StringIO())

        monkeypatch.setattr(net, 'urlopen', bad_urlopen)
        with pytest.raises(RuntimeError):
            net.get_request('https://example.ceph.com')
