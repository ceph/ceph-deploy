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


class TestIsUpstart(object):

    def test_it_is_actually_systemd(self):
        fake_conn = Mock()
        fake_conn.remote_module.grep = Mock(return_value=True)
        result = system.is_upstart(fake_conn)
        assert result is False

    def test_no_initctl(self):
        fake_conn = Mock()
        fake_conn.remote_module.grep = Mock(return_value=False)
        fake_conn.remote_module.which = Mock(return_value=None)
        result = system.is_upstart(fake_conn)
        assert result is False

    def test_initctl_version_says_upstart(self, monkeypatch):
        fake_conn = Mock()
        fake_conn.remote_module.grep = Mock(return_value=False)
        fake_conn.remote_module.which = Mock(return_value='/bin/initctl')
        fake_stdout = ([b'init', b'(upstart 1.12.1)'], [], 0)
        fake_check = Mock(return_value=fake_stdout)
        monkeypatch.setattr("ceph_deploy.util.system.remoto.process.check", lambda *a: fake_check())

        result = system.is_upstart(fake_conn)
        assert result is True

    def test_initctl_version_says_something_else(self, monkeypatch):
        fake_conn = Mock()
        fake_conn.remote_module.grep = Mock(return_value=False)
        fake_conn.remote_module.which = Mock(return_value='/bin/initctl')
        fake_stdout = ([b'nosh', b'version', b'1.14'], [], 0)
        fake_check = Mock(return_value=fake_stdout)
        monkeypatch.setattr("ceph_deploy.util.system.remoto.process.check", lambda *a: fake_check())

        result = system.is_upstart(fake_conn)
        assert result is False
