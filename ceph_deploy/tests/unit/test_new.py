from ceph_deploy import new
from ceph_deploy.tests import util
import pytest


class TestValidateHostIp(object):

    def test_for_all_subnets_all_ips_match(self):
        ips = util.generate_ips("10.0.0.1", "10.0.0.40")
        ips.extend(util.generate_ips("10.0.1.1", "10.0.1.40"))
        subnets = ["10.0.0.1/16", "10.0.1.1/16"]
        assert new.validate_host_ip(ips, subnets) is None

    def test_all_subnets_have_one_matching_ip(self):
        ips = util.generate_ips("10.0.0.1", "10.0.0.40")
        ips.extend(util.generate_ips("10.0.1.1", "10.0.1.40"))
        # regardless of extra IPs that may not match. The requirement
        # is already satisfied
        ips.extend(util.generate_ips("10.1.2.1", "10.1.2.40"))
        subnets = ["10.0.0.1/16", "10.0.1.1/16"]
        assert new.validate_host_ip(ips, subnets) is None

    def test_not_all_subnets_have_one_matching_ip(self):
        ips = util.generate_ips("10.0.0.1", "10.0.0.40")
        ips.extend(util.generate_ips("10.0.1.1", "10.0.1.40"))
        subnets = ["10.0.0.1/16", "10.1.1.1/16"]
        with pytest.raises(RuntimeError):
            new.validate_host_ip(ips, subnets)
