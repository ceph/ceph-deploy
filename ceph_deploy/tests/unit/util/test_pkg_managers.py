from mock import patch, Mock
from ceph_deploy.util import pkg_managers


class TestApt(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Apt(Mock()).install('vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Apt(Mock()).install(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Apt(Mock()).remove('vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Apt(Mock()).remove(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']


class TestYum(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Yum(Mock()).install('vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Yum(Mock()).install(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Yum(Mock()).remove('vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Yum(Mock()).remove(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']


class TestZypper(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'
        self.to_check = 'ceph_deploy.util.pkg_managers.remoto.process.check'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Zypper(Mock()).install('vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.Zypper(Mock()).install(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_check = Mock()
        fake_check.return_value = '', '', 0
        with patch(self.to_check, fake_check):
            pkg_managers.Zypper(Mock()).remove('vim')
            result = fake_check.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_check = Mock()
        fake_check.return_value = '', '', 0
        with patch(self.to_check, fake_check):
            pkg_managers.Zypper(Mock()).remove(['vim', 'zsh'])
            result = fake_check.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']


class TestDNF(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.DNF(Mock()).install('vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.DNF(Mock()).install(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.DNF(Mock()).remove('vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.DNF(Mock()).remove(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]


class TestAtpRpm(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.AptRpm(Mock()).install('vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.AptRpm(Mock()).install(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.AptRpm(Mock()).remove('vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.AptRpm(Mock()).remove(['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

