from mock import patch
from ceph_deploy.hosts import remotes
from ceph_deploy.hosts.remotes import platform_information

class FakeExists(object):

    def __init__(self, existing_paths):
        self.existing_paths = existing_paths

    def __call__(self, path):
        for existing_path in self.existing_paths:
            if path == existing_path:
                return path


class TestWhich(object):

    def setup(self):
        self.exists_module = 'ceph_deploy.hosts.remotes.os.path.exists'

    def test_finds_absolute_paths(self):
        exists = FakeExists(['/bin/ls'])
        with patch(self.exists_module, exists):
            path = remotes.which('ls')
        assert path == '/bin/ls'

    def test_does_not_find_executable(self):
        exists = FakeExists(['/bin/foo'])
        with patch(self.exists_module, exists):
            path = remotes.which('ls')
        assert path is None

class TestPlatformInformation(object):
    """ tests various inputs that remotes.platform_information handles

    you can test your OS string by comparing the results with the output from:
      python -c "import platform; print platform.linux_distribution()"
    """

    def setup(self):
        pass

    def test_handles_deb_version_num(self):
        def fake_distro(): return ('debian', '8.4', '')
        distro, release, codename = platform_information(fake_distro)
        assert distro == 'debian'
        assert release == '8.4'
        assert codename == 'jessie'

    def test_handles_deb_version_slash(self):
        def fake_distro(): return ('debian', 'wheezy/something', '')
        distro, release, codename = platform_information(fake_distro)
        assert distro == 'debian'
        assert release == 'wheezy/something'
        assert codename == 'wheezy'

    def test_handles_deb_version_slash_sid(self):
        def fake_distro(): return ('debian', 'jessie/sid', '')
        distro, release, codename = platform_information(fake_distro)
        assert distro == 'debian'
        assert release == 'jessie/sid'
        assert codename == 'sid'

    def test_handles_no_codename(self):
        def fake_distro(): return ('SlaOS', '99.999', '')
        distro, release, codename = platform_information(fake_distro)
        assert distro == 'SlaOS'
        assert release == '99.999'
        assert codename == ''

    # Normal distro strings
    def test_hanles_centos_64(self):
        def fake_distro(): return ('CentOS', '6.4', 'Final')
        distro, release, codename = platform_information(fake_distro)
        assert distro == 'CentOS'
        assert release == '6.4'
        assert codename == 'Final'


    def test_handles_ubuntu_percise(self):
        def fake_distro(): return ('Ubuntu', '12.04', 'precise')
        distro, release, codename = platform_information(fake_distro)
        assert distro == 'Ubuntu'
        assert release == '12.04'
        assert codename == 'precise'
