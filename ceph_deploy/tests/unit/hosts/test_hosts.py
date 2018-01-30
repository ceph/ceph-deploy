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

    def test_get_mint(self):
        result = hosts._normalized_distro_name('LinuxMint')
        assert result == 'ubuntu'

    def test_get_suse(self):
        result = hosts._normalized_distro_name('SUSE LINUX')
        assert result == 'suse'

    def test_get_redhat(self):
        result = hosts._normalized_distro_name('RedHatEnterpriseLinux')
        assert result == 'redhat'

    def test_get_virtuozzo(self):
        result = hosts._normalized_distro_name('Virtuozzo Linux')
        assert result == 'virtuozzo'

    def test_get_arch(self):
        result = hosts._normalized_distro_name('Arch Linux')
        assert result == 'arch'


class TestNormalizeRelease(object):

    def test_int_single_version(self):
        result = hosts._normalized_release('1')
        assert result.int_major == 1
        assert result.int_minor == 0
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_single_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1')
        assert result.int_major == 1
        assert result.int_minor == 0
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_single_version_with_prepended_zero(self):
        result = hosts._normalized_release('01')
        assert result.int_major == 1
        assert result.int_minor == 0
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_minor_version(self):
        result = hosts._normalized_release('1.8')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_minor_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1.8')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_minor_version_with_prepended_zero(self):
        result = hosts._normalized_release('01.08')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_patch_version(self):
        result = hosts._normalized_release('1.8.1234')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 0

    def test_int_patch_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1.8.1234')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 0

    def test_int_patch_version_with_prepended_zero(self):
        result = hosts._normalized_release('01.08.01234')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 0

    def test_int_garbage_version(self):
        result = hosts._normalized_release('1.8.1234.1')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 1

    def test_int_garbage_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1.8.1234.1')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 1

    def test_int_garbage_version_with_prepended_zero(self):
        result = hosts._normalized_release('01.08.01234.1')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 1

    def test_int_single_version_rc(self):
        result = hosts._normalized_release('1rc-123')
        assert result.int_major == 1
        assert result.int_minor == 0
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_single_version_with_trailing_space_rc(self):
        result = hosts._normalized_release(' 1rc-123')
        assert result.int_major == 1
        assert result.int_minor == 0
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_single_version_with_prepended_zero_rc(self):
        result = hosts._normalized_release('01rc-123')
        assert result.int_major == 1
        assert result.int_minor == 0
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_minor_version_rc(self):
        result = hosts._normalized_release('1.8rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_minor_version_with_trailing_space_rc(self):
        result = hosts._normalized_release(' 1.8rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_minor_version_with_prepended_zero_rc(self):
        result = hosts._normalized_release('01.08rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 0
        assert result.int_garbage == 0

    def test_int_patch_version_rc(self):
        result = hosts._normalized_release('1.8.1234rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 0

    def test_int_patch_version_with_trailing_space_rc(self):
        result = hosts._normalized_release(' 1.8.1234rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 0

    def test_int_patch_version_with_prepended_zero_rc(self):
        result = hosts._normalized_release('01.08.01234rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 0

    def test_int_garbage_version_rc(self):
        result = hosts._normalized_release('1.8.1234.1rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 1

    def test_int_garbage_version_with_trailing_space_rc(self):
        result = hosts._normalized_release(' 1.8.1234.1rc-123')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 1

    def test_int_garbage_version_with_prepended_zero_rc(self):
        result = hosts._normalized_release('01.08.01234.1rc-1')
        assert result.int_major == 1
        assert result.int_minor == 8
        assert result.int_patch == 1234
        assert result.int_garbage == 1

    # with non ints

    def test_single_version(self):
        result = hosts._normalized_release('1')
        assert result.major == "1"
        assert result.minor == "0"
        assert result.patch == "0"
        assert result.garbage == "0"

    def test_single_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1')
        assert result.major == "1"
        assert result.minor == "0"
        assert result.patch == "0"
        assert result.garbage == "0"

    def test_single_version_with_prepended_zero(self):
        result = hosts._normalized_release('01')
        assert result.major == "01"
        assert result.minor == "0"
        assert result.patch == "0"
        assert result.garbage == "0"

    def test_minor_version(self):
        result = hosts._normalized_release('1.8')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "0"
        assert result.garbage == "0"

    def test_minor_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1.8')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "0"
        assert result.garbage == "0"

    def test_minor_version_with_prepended_zero(self):
        result = hosts._normalized_release('01.08')
        assert result.major == "01"
        assert result.minor == "08"
        assert result.patch == "0"
        assert result.garbage == "0"

    def test_patch_version(self):
        result = hosts._normalized_release('1.8.1234')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234"
        assert result.garbage == "0"

    def test_patch_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1.8.1234')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234"
        assert result.garbage == "0"

    def test_patch_version_with_prepended_zero(self):
        result = hosts._normalized_release('01.08.01234')
        assert result.major == "01"
        assert result.minor == "08"
        assert result.patch == "01234"
        assert result.garbage == "0"

    def test_garbage_version(self):
        result = hosts._normalized_release('1.8.1234.1')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234"
        assert result.garbage == "1"

    def test_garbage_version_with_trailing_space(self):
        result = hosts._normalized_release(' 1.8.1234.1')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234"
        assert result.garbage == "1"

    def test_garbage_version_with_prepended_zero(self):
        result = hosts._normalized_release('01.08.01234.1')
        assert result.major == "01"
        assert result.minor == "08"
        assert result.patch == "01234"
        assert result.garbage == "1"

    def test_patch_version_rc(self):
        result = hosts._normalized_release('1.8.1234rc-123')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234rc-123"
        assert result.garbage == "0"

    def test_patch_version_with_trailing_space_rc(self):
        result = hosts._normalized_release(' 1.8.1234rc-123')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234rc-123"
        assert result.garbage == "0"

    def test_patch_version_with_prepended_zero_rc(self):
        result = hosts._normalized_release('01.08.01234.1rc-123')
        assert result.major == "01"
        assert result.minor == "08"
        assert result.patch == "01234"
        assert result.garbage == "1rc-123"

    def test_garbage_version_rc(self):
        result = hosts._normalized_release('1.8.1234.1rc-123')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234"
        assert result.garbage == "1rc-123"

    def test_garbage_version_with_trailing_space_rc(self):
        result = hosts._normalized_release(' 1.8.1234.1rc-123')
        assert result.major == "1"
        assert result.minor == "8"
        assert result.patch == "1234"
        assert result.garbage == "1rc-123"

    def test_garbage_version_with_prepended_zero_rc(self):
        result = hosts._normalized_release('01.08.01234.1rc-1')
        assert result.major == "01"
        assert result.minor == "08"
        assert result.patch == "01234"
        assert result.garbage == "1rc-1"

    def test_garbage_version_with_no_numbers(self):
        result = hosts._normalized_release('sid')
        assert result.major == "sid"
        assert result.minor == "0"
        assert result.patch == "0"
        assert result.garbage == "0"


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

    def test_get_oracle(self):
        result = hosts._get_distro('Oracle Linux Server')
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

    def test_get_mint(self):
        result = hosts._get_distro('LinuxMint')
        assert result.__name__.endswith('debian')

    def test_get_virtuozzo(self):
        result = hosts._get_distro('Virtuozzo Linux')
        assert result.__name__.endswith('centos')

    def test_get_arch(self):
        result = hosts._get_distro('Arch Linux')
        assert result.__name__.endswith('arch')
