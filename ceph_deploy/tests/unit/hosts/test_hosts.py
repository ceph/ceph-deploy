from pytest import raises

from ceph_deploy import exc
from ceph_deploy import hosts


class TestNormalized(object):

    def test_get_debian(self):
        result = hosts._normalized_distro_name('Debian')
        assert result == 'debian'

    def test_get_ubuntu(self):
        result = hosts._normalized_distro_name('Ubuntu')
        assert result == 'ubuntu'

    def test_get_suse(self):
        result = hosts._normalized_distro_name('SUSE LINUX')
        assert result == 'suse'

    def test_get_redhat(self):
        result = hosts._normalized_distro_name('RedHatEnterpriseLinux')
        assert result == 'redhat'


class TestGetDistro(object):

    def test_get_debian(self):
        result = hosts._get_distro('Debian')
        assert result.__name__.endswith('debian')

    def test_get_ubuntu(self):
        # Ubuntu imports debian stuff
        result = hosts._get_distro('Ubuntu')
        assert result.__name__.endswith('debian')

    def test_get_centos(self):
        result = hosts._get_distro('CentOS')
        assert result.__name__.endswith('centos')

    def test_get_scientific(self):
        result = hosts._get_distro('Scientific')
        assert result.__name__.endswith('centos')

    def test_get_redhat(self):
        result = hosts._get_distro('RedHat')
        assert result.__name__.endswith('centos')

    def test_get_uknown(self):
        with raises(exc.UnsupportedPlatform):
            hosts._get_distro('Solaris')

    def test_get_fallback(self):
        result = hosts._get_distro('Solaris', 'Debian')
        assert result.__name__.endswith('debian')
