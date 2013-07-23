from mock import Mock, MagicMock, patch, call
from ceph_deploy import mon


def path_exists(target_paths=None):
    """
    A quick helper that enforces a check for the existence of a path. Since we
    are dealing with fakes, we allow to pass in a list of paths that are OK to
    return True, otherwise return False.
    """
    target_paths = target_paths or []

    def exists(path):
        return path in target_paths
    return exists


def mock_open(mock=None, data=None):
    """
    Fake the behavior of `open` when used as a context manager
    """
    if mock is None:
        mock = MagicMock(spec=file)

    handle = MagicMock(spec=file)
    handle.write.return_value = None
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


class TestCreateMon(object):

    def setup(self):
        # this setup is way more verbose than normal
        # but we are forced to because this function needs a lot
        # passed in for remote execution. No other way around it.
        self.socket = Mock()
        self.socket.gethostname.return_value = 'hostname'
        self.fake_write = Mock(name='fake_write')
        self.fake_file = mock_open(data=self.fake_write)
        self.os = Mock()
        self.sprocess = Mock()
        self.paths = Mock()
        self.paths.mon.path = Mock(return_value='/cluster-hostname')

    def test_create_mon_tmp_path_if_nonexistent(self):
        self.os.path.exists = Mock(
            side_effect=path_exists(['/cluster-hostname']))
        self.paths.mon.constants.tmp_path = '/var/lib/ceph/tmp'
        with patch('__builtin__.file', self.fake_file):
            mon.create_mon(
                'cluster', '1234', 'initd',
                paths=self.paths, os=self.os, subprocess=self.sprocess,
                socket=self.socket)

        result = self.os.makedirs.call_args_list[0]
        assert result == call('/var/lib/ceph/tmp')

    def test_create_mon_path_if_nonexistent(self):
        self.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        with patch('__builtin__.file', self.fake_file):
            mon.create_mon(
                'cluster', '1234', 'initd',
                paths=self.paths, os=self.os, subprocess=self.sprocess,
                socket=self.socket)

        result = self.os.makedirs.call_args_list[0]
        assert result == call('/cluster-hostname')

    def test_write_keyring(self):
        self.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        with patch('__builtin__.file', self.fake_file):
            mon.create_mon(
                'cluster', '1234', 'initd',
                paths=self.paths, os=self.os, subprocess=self.sprocess,
                socket=self.socket)

        result = self.fake_write.write.call_args_list[0]
        assert result == call('1234')

    def test_write_done_path(self):
        self.paths.mon.done = Mock(return_value='/cluster-hostname/done')
        self.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        with patch('__builtin__.file', self.fake_file):
            mon.create_mon(
                'cluster', '1234', 'initd',
                paths=self.paths, os=self.os, subprocess=self.sprocess,
                socket=self.socket)

        result = self.fake_file.call_args_list[1]
        assert result == call('/cluster-hostname/done', 'w')

    def test_write_init_path(self):
        self.paths.mon.init = Mock(return_value='/cluster-hostname/init')
        self.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        with patch('__builtin__.file', self.fake_file):
            mon.create_mon(
                'cluster', '1234', 'initd',
                paths=self.paths, os=self.os, subprocess=self.sprocess,
                socket=self.socket)

        result = self.fake_file.call_args_list[2]
        assert result == call('/cluster-hostname/init', 'w')


class TestIsRunning(object):

    def setup(self):
        self.fake_popen = Mock()
        self.fake_popen.return_value = self.fake_popen

    def test_is_running_centos(self):
        centos_out = ['', "mon.mire094: running {'version': '0.6.15'}"]
        self.fake_popen.communicate = Mock(return_value=centos_out)
        with patch('ceph_deploy.mon.subprocess.Popen', self.fake_popen):
            result = mon.is_running(['ceph', 'status'])
        assert result is True

    def test_is_not_running_centos(self):
        centos_out = ['', "mon.mire094: not running {'version': '0.6.15'}"]
        self.fake_popen.communicate = Mock(return_value=centos_out)
        with patch('ceph_deploy.mon.subprocess.Popen', self.fake_popen):
            result = mon.is_running(['ceph', 'status'])
        assert result is False

    def test_is_dead_centos(self):
        centos_out = ['', "mon.mire094: dead {'version': '0.6.15'}"]
        self.fake_popen.communicate = Mock(return_value=centos_out)
        with patch('ceph_deploy.mon.subprocess.Popen', self.fake_popen):
            result = mon.is_running(['ceph', 'status'])
        assert result is False

    def test_is_running_ubuntu(self):
        ubuntu_out = ['', "ceph-mon (ceph/mira103) start/running, process 5866"]
        self.fake_popen.communicate = Mock(return_value=ubuntu_out)
        with patch('ceph_deploy.mon.subprocess.Popen', self.fake_popen):
            result = mon.is_running(['ceph', 'status'])
        assert result is True

    def test_is_not_running_ubuntu(self):
        ubuntu_out = ['', "ceph-mon (ceph/mira103) start/dead, process 5866"]
        self.fake_popen.communicate = Mock(return_value=ubuntu_out)
        with patch('ceph_deploy.mon.subprocess.Popen', self.fake_popen):
            result = mon.is_running(['ceph', 'status'])
        assert result is False

    def test_is_dead_ubuntu(self):
        ubuntu_out = ['', "ceph-mon (ceph/mira103) stop/not running, process 5866"]
        self.fake_popen.communicate = Mock(return_value=ubuntu_out)
        with patch('ceph_deploy.mon.subprocess.Popen', self.fake_popen):
            result = mon.is_running(['ceph', 'status'])
        assert result is False
