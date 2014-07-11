from mock import Mock
from pytest import raises
from ceph_deploy.util import system
from ceph_deploy import exc


class TestExecutablePath(object):

    def test_returns_path(self):
        fake_conn = Mock()
        fake_conn.remote_module.which = Mock(return_value='/path')
        result = system.executable_path(fake_conn, 'foo')
        assert result == '/path'

    def test_cannot_find_executable(self):
        fake_conn = Mock()
        fake_conn.remote_module.which = Mock(return_value=None)
        with raises(exc.ExecutableNotFound):
            system.executable_path(fake_conn, 'foo')
