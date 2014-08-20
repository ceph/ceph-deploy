from ceph_deploy.util import net
import pytest


def generate_ips(start_ip, end_ip):
    start = list(map(int, start_ip.split(".")))
    end = list(map(int, end_ip.split(".")))
    temp = start
    ip_range = []

    ip_range.append(start_ip)
    while temp != end:
        start[3] += 1
        for i in (3, 2, 1):
            if temp[i] == 256:
                temp[i] = 0
                temp[i-1] += 1
        ip_range.append(".".join(map(str, temp)))

    return ip_range


# The following class adds about 1900 tests via py.test generation

class TestIpInSubnet(object):

    @pytest.mark.parametrize('ip', generate_ips("10.0.0.1", "10.0.0.255"))
    def test_correct_for_10_0_0_255(self, ip):
        assert net.ip_in_subnet(ip, "10.0.0.0/16")

    @pytest.mark.parametrize('ip', generate_ips("10.0.0.1", "10.0.0.255"))
    def test_false_for_10_0_0_255(self, ip):
        assert net.ip_in_subnet(ip, "10.2.0.0/24") is False

    @pytest.mark.parametrize('ip', generate_ips("255.255.255.1", "255.255.255.255"))
    def test_false_for_255_addresses(self, ip):
        assert net.ip_in_subnet(ip, "10.9.1.0/16") is False

    @pytest.mark.parametrize('ip', generate_ips("172.7.1.1", "172.7.1.255"))
    def test_false_for_172_addresses(self, ip):
        assert net.ip_in_subnet(ip, "172.3.0.0/16") is False

    @pytest.mark.parametrize('ip', generate_ips("10.9.8.0", "10.9.8.255"))
    def test_true_for_16_subnets(self, ip):
        assert net.ip_in_subnet(ip, "10.9.1.0/16") is True

    @pytest.mark.parametrize('ip', generate_ips("10.9.8.0", "10.9.8.255"))
    def test_false_for_24_subnets(self, ip):
        assert net.ip_in_subnet(ip, "10.9.1.0/24") is False
