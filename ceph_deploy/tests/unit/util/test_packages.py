from mock import Mock, patch
from ceph_deploy.exc import ExecutableNotFound
from ceph_deploy.util import packages


class TestCephIsInstalled(object):

    def test_installed(self):
        with patch('ceph_deploy.util.packages.system'):
            c = packages.Ceph(Mock())
            assert c.installed is True

    def test_not_installed(self):
        with patch('ceph_deploy.util.packages.system') as fsystem:
            bad_executable = Mock(
                side_effect=ExecutableNotFound('host', 'ceph')
            )
            fsystem.executable_path = bad_executable
            c = packages.Ceph(Mock())
            assert c.installed is False


class TestCephVersion(object):

    def test_executable_not_found(self):
        with patch('ceph_deploy.util.packages.system') as fsystem:
            bad_executable = Mock(
                side_effect=ExecutableNotFound('host', 'ceph')
            )
            fsystem.executable_path = bad_executable
            c = packages.Ceph(Mock())
            assert c._get_version_output() == ''

    def test_output_is_unusable(self):
        _check = Mock(return_value=(b'', b'', 1))
        c = packages.Ceph(Mock(), _check=_check)
        assert c._get_version_output() == ''

    def test_output_usable(self):
        version = b'ceph version 9.0.1-kjh234h123hd (asdf78asdjh234)'
        _check = Mock(return_value=(version, b'', 1))
        c = packages.Ceph(Mock(), _check=_check)
        assert c._get_version_output() == '9.0.1-kjh234h123hd'
