from ceph_deploy.hosts import centos
from mock import Mock


class TestCentosUrlPart(object):

    def setup(self):
        self.distro = Mock()

    def test_url_fallsback_to_el6(self):
        assert centos.repository_url_part(self.distro) == 'el6'

    def test_url_detects_rhel6(self):
        self.distro.normalized_name = 'redhat'
        assert centos.repository_url_part(self.distro) == 'rhel6'

    def test_url_detects_rhel5(self):
        self.distro.normalized_name = 'redhat'
        self.distro.release = '5.0'
        assert centos.repository_url_part(self.distro) == 'el6'

