from ceph_deploy.hosts import centos
from mock import Mock

class TestCentosVersionDetection(object):

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

    def test_url_detects_rhel7(self):
        self.distro.normalized_name = 'redhat'
        self.distro.release = '7.0'
        assert centos.repository_url_part(self.distro) == 'rhel7'

    def test_rpm_dist_fallsback_to_el6(self):
        self.distro.normalized_name = 'redhat'
        self.distro.release = '3'
        assert centos.rpm_dist(self.distro) == 'el6'

    def test_rpm_dist_detects_rhel6(self):
        self.distro.normalized_name = 'redhat'
        self.distro.release = '6.6'
        assert centos.rpm_dist(self.distro) == 'el6'

    def test_rpm_dist_detects_rhel7(self):
        self.distro.normalized_name = 'redhat'
        self.distro.release = '7.0'
        assert centos.rpm_dist(self.distro) == 'el7'

    def test_url_fallsback_to_el6_centos(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = ''
        assert centos.repository_url_part(self.distro) == 'el6'

    def test_url_detects_el5(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = '5.0'
        assert centos.repository_url_part(self.distro) == 'el6'

    def test_url_detects_el6(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = '6.0'
        assert centos.repository_url_part(self.distro) == 'el6'

    def test_url_detects_el7(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = '7.0'
        assert centos.repository_url_part(self.distro) == 'el7'

    def test_rpm_dist_fallsback_to_el6_centos(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = '5'
        assert centos.rpm_dist(self.distro) == 'el6'

    def test_rpm_dist_detects_el6_centos(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = '6.6'
        assert centos.rpm_dist(self.distro) == 'el6'

    def test_rpm_dist_detects_el7(self):
        self.distro.normalized_name = 'centos'
        self.distro.release = '7.0'
        assert centos.rpm_dist(self.distro) == 'el7'
