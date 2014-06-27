from mock import patch, Mock
from ceph_deploy.util import pkg_managers


class TestRPM(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_normal_flags(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.rpm(Mock())
            result = fake_run.call_args_list[-1]
        assert result[0][-1] == ['rpm', '-Uvh']

    def test_extended_flags(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.rpm(
                Mock(),
                ['-f', 'vim'])
            result = fake_run.call_args_list[-1]
        assert result[0][-1] == ['rpm', '-Uvh', '-f', 'vim']


class TestApt(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.apt(Mock(), 'vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.apt(Mock(), ['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.apt_remove(Mock(), 'vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.apt_remove(Mock(), ['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']


class TestYum(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.yum(Mock(), 'vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.yum(Mock(), ['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.yum_remove(Mock(), 'vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.yum_remove(Mock(), ['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']


class TestZypper(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.remoto.process.run'

    def test_install_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.zypper(Mock(), 'vim')
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_install_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.zypper(Mock(), ['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'install' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

    def test_remove_single_package(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.zypper_remove(Mock(), 'vim')
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-1] == 'vim'

    def test_remove_multiple_packages(self):
        fake_run = Mock()
        with patch(self.to_patch, fake_run):
            pkg_managers.zypper_remove(Mock(), ['vim', 'zsh'])
            result = fake_run.call_args_list[-1]
        assert 'remove' in result[0][-1]
        assert result[0][-1][-2:] == ['vim', 'zsh']

