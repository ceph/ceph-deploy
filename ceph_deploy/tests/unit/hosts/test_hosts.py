from pytest import raises
from mock import Mock, patch

from ceph_deploy import exc
from ceph_deploy import hosts


class TestNormalized(object):

    def test_get_debian(self):
        result = hosts._normalized_distro_name('Debian')
        assert result == 'debian'

    def test_get_centos(self):
        result = hosts._normalized_distro_name('CentOS Linux')
        assert result == 'centos'

    def test_get_ubuntu(self):
        result = hosts._normalized_distro_name('Ubuntu')
        assert result == 'ubuntu'

    def test_get_suse(self):
        result = hosts._normalized_distro_name('SUSE LINUX')
        assert result == 'suse'

    def test_get_redhat(self):
        result = hosts._normalized_distro_name('RedHatEnterpriseLinux')
        assert result == 'redhat'


class TestHostGet(object):

    def make_fake_connection(self, platform_information=None):
        get_connection = Mock()
        get_connection.return_value = get_connection
        get_connection.remote_module.platform_information = Mock(
            return_value=platform_information)
        return get_connection

    def test_get_unsupported(self):
        fake_get_connection = self.make_fake_connection(('Solaris Enterprise', '', ''))
        with patch('ceph_deploy.hosts.get_connection', fake_get_connection):
            with raises(exc.UnsupportedPlatform):
                hosts.get('myhost')

    def test_get_unsupported_message(self):
        fake_get_connection = self.make_fake_connection(('Solaris Enterprise', '', ''))
        with patch('ceph_deploy.hosts.get_connection', fake_get_connection):
            with raises(exc.UnsupportedPlatform) as error:
                hosts.get('myhost')

        assert error.value.__str__() == 'Platform is not supported: Solaris Enterprise  '

    def test_get_unsupported_message_release(self):
        fake_get_connection = self.make_fake_connection(('Solaris', 'Tijuana', '12'))
        with patch('ceph_deploy.hosts.get_connection', fake_get_connection):
            with raises(exc.UnsupportedPlatform) as error:
                hosts.get('myhost')

        assert error.value.__str__() == 'Platform is not supported: Solaris 12 Tijuana'



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

    def test_get_redhat_whitespace(self):
        result = hosts._get_distro('Red Hat Enterprise Linux')
        assert result.__name__.endswith('centos')

    def test_get_uknown(self):
        assert hosts._get_distro('Solaris') is None

    def test_get_fallback(self):
        result = hosts._get_distro('Solaris', 'Debian')
        assert result.__name__.endswith('debian')
