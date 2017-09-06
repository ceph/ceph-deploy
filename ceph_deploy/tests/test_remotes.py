from mock import patch
from ceph_deploy.hosts import remotes
from ceph_deploy.hosts.remotes import platform_information, parse_os_release

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

class TestParseOsRelease(object):
    """ test various forms of /etc/os-release """

    def setup(self):
        pass

    def test_handles_centos_7(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
NAME="CentOS Linux"
VERSION="7 (Core)"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="7"
PRETTY_NAME="CentOS Linux 7 (Core)"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:centos:centos:7"
HOME_URL="https://www.centos.org/"
BUG_REPORT_URL="https://bugs.centos.org/"

CENTOS_MANTISBT_PROJECT="CentOS-7"
CENTOS_MANTISBT_PROJECT_VERSION="7"
REDHAT_SUPPORT_PRODUCT="centos"
REDHAT_SUPPORT_PRODUCT_VERSION="7"
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'centos'
        assert release == '7'
        assert codename == 'core'


    def test_handles_debian_stretch(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
PRETTY_NAME="Debian GNU/Linux 9 (stretch)"
NAME="Debian GNU/Linux"
VERSION_ID="9"
VERSION="9 (stretch)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'debian'
        assert release == '9'
        assert codename == 'stretch'

    def test_handles_fedora_26(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
NAME=Fedora
VERSION="26 (Twenty Six)"
ID=fedora
VERSION_ID=26
PRETTY_NAME="Fedora 26 (Twenty Six)"
ANSI_COLOR="0;34"
CPE_NAME="cpe:/o:fedoraproject:fedora:26"
HOME_URL="https://fedoraproject.org/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
REDHAT_BUGZILLA_PRODUCT="Fedora"
REDHAT_BUGZILLA_PRODUCT_VERSION=26
REDHAT_SUPPORT_PRODUCT="Fedora"
REDHAT_SUPPORT_PRODUCT_VERSION=26
PRIVACY_POLICY_URL=https://fedoraproject.org/wiki/Legal:PrivacyPolicy
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'fedora'
        assert release == '26'
        assert codename == 'twenty six'

    def test_handles_opensuse_leap_42_2(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
NAME="openSUSE Leap"
VERSION="42.2"
ID=opensuse
ID_LIKE="suse"
VERSION_ID="42.2"
PRETTY_NAME="openSUSE Leap 42.2"
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:opensuse:leap:42.2"
BUG_REPORT_URL="https://bugs.opensuse.org"
HOME_URL="https://www.opensuse.org/"
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'opensuse'
        assert release == '42.2'
        assert codename == '42.2'

    def test_handles_opensuse_tumbleweed(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
NAME="openSUSE Tumbleweed"
# VERSION="20170502"
ID=opensuse
ID_LIKE="suse"
VERSION_ID="20170502"
PRETTY_NAME="openSUSE Tumbleweed"
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:opensuse:tumbleweed:20170502"
BUG_REPORT_URL="https://bugs.opensuse.org"
HOME_URL="https://www.opensuse.org/"
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'opensuse'
        assert release == '20170502'
        assert codename == 'tumbleweed'

    def test_handles_sles_12_sp3(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
NAME="SLES"
VERSION="12-SP3"
VERSION_ID="12.3"
PRETTY_NAME="SUSE Linux Enterprise Server 12 SP3"
ID="sles"
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:suse:sles:12:sp3"
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'sles'
        assert release == '12.3'
        assert codename == '12-SP3'

    def test_handles_ubuntu_xenial(self, tmpdir):
        path = str(tmpdir.join('os_release'))
        with open(path, 'w') as os_release:
            os_release.write("""
NAME="Ubuntu"
VERSION="16.04 LTS (Xenial Xerus)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 16.04 LTS"
VERSION_ID="16.04"
HOME_URL="http://www.ubuntu.com/"
SUPPORT_URL="http://help.ubuntu.com/"
BUG_REPORT_URL="http://bugs.launchpad.net/ubuntu/"
UBUNTU_CODENAME=xenial
""")
        distro, release, codename = parse_os_release(path)
        assert distro == 'ubuntu'
        assert release == '16.04'
        assert codename == 'xenial'
