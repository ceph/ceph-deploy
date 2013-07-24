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
