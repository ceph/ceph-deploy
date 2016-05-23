import sys
import py.test
from mock import Mock, patch
# the below import of mock again is to workaround a py.test issue:
# https://github.com/pytest-dev/pytest/issues/1035
import mock
from ceph_deploy import mon
from ceph_deploy.hosts.common import mon_create
from ceph_deploy.misc import mon_hosts, remote_shortname


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


@py.test.mark.skipif(reason='failing due to removal of pushy')
class TestCreateMon(object):

    def setup(self):
        # this setup is way more verbose than normal
        # but we are forced to because this function needs a lot
        # passed in for remote execution. No other way around it.
        self.socket = Mock()
        self.socket.gethostname.return_value = 'hostname'
        self.fake_file = mock.mock_open()
        self.distro = Mock()
        self.sprocess = Mock()
        self.paths = Mock()
        self.paths.mon.path = Mock(return_value='/cluster-hostname')
        self.logger = Mock()
        self.logger.info = self.logger.debug = lambda x: sys.stdout.write(str(x) + "\n")

    def test_create_mon_tmp_path_if_nonexistent(self):
        self.distro.sudo_conn.modules.os.path.exists = Mock(
            side_effect=path_exists(['/cluster-hostname']))
        self.paths.mon.constants.tmp_path = '/var/lib/ceph/tmp'
        args = Mock(return_value=['cluster', '1234', 'initd'])
        args.cluster = 'cluster'
        with patch('ceph_deploy.hosts.common.conf.load'):
            mon_create(self.distro, args, Mock(), 'hostname')

        result = self.distro.conn.remote_module.create_mon_path.call_args_list[-1]
        assert result ==mock.call('/var/lib/ceph/mon/cluster-hostname')

    def test_write_keyring(self):
        self.distro.sudo_conn.modules.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        args = Mock(return_value=['cluster', '1234', 'initd'])
        args.cluster = 'cluster'
        with patch('ceph_deploy.hosts.common.conf.load'):
            with patch('ceph_deploy.hosts.common.remote') as fake_remote:
                mon_create(self.distro, self.logger, args, Mock(), 'hostname')

        # the second argument to `remote()` should be the write func
        result = fake_remote.call_args_list[1][0][-1].__name__
        assert result == 'write_monitor_keyring'

    def test_write_done_path(self):
        self.distro.sudo_conn.modules.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        args = Mock(return_value=['cluster', '1234', 'initd'])
        args.cluster = 'cluster'

        with patch('ceph_deploy.hosts.common.conf.load'):
            with patch('ceph_deploy.hosts.common.remote') as fake_remote:
                mon_create(self.distro, self.logger, args, Mock(), 'hostname')

        # the second to last argument to `remote()` should be the done path
        # write
        result = fake_remote.call_args_list[-2][0][-1].__name__
        assert result == 'create_done_path'

    def test_write_init_path(self):
        self.distro.sudo_conn.modules.os.path.exists = Mock(
            side_effect=path_exists(['/']))
        args = Mock(return_value=['cluster', '1234', 'initd'])
        args.cluster = 'cluster'

        with patch('ceph_deploy.hosts.common.conf.load'):
            with patch('ceph_deploy.hosts.common.remote') as fake_remote:
                mon_create(self.distro, self.logger, args, Mock(), 'hostname')

        result = fake_remote.call_args_list[-1][0][-1].__name__
        assert result == 'create_init_path'

    def test_mon_hosts(self):
        hosts = Mock()
        for (name, host) in mon_hosts(('name1', 'name2.localdomain',
                    'name3:1.2.3.6', 'name4:localhost.localdomain')):
            hosts.get(name, host)

        expected = [mock.call.get('name1', 'name1'),
                   mock.call.get('name2', 'name2.localdomain'),
                   mock.call.get('name3', '1.2.3.6'),
                   mock.call.get('name4', 'localhost.localdomain')]
        result = hosts.mock_calls
        assert result == expected

    def test_remote_shortname_fqdn(self):
        socket = Mock()
        socket.gethostname.return_value = 'host.f.q.d.n'
        assert remote_shortname(socket) == 'host'

    def test_remote_shortname_host(self):
        socket = Mock()
        socket.gethostname.return_value = 'host'
        assert remote_shortname(socket) == 'host'


@py.test.mark.skipif(reason='failing due to removal of pushy')
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


class TestKeyringParser(object):

    def test_line_ends_with_newline_char(self, tmpdir):
        keyring = tmpdir.join('foo.mon.keyring')
        keyring.write('[section]\nasdfasdf\nkey = value')
        result = mon.keyring_parser(keyring.strpath)

        assert result == ['section']

    def test_line_does_not_end_with_newline_char(self, tmpdir):
        keyring = tmpdir.join('foo.mon.keyring')
        keyring.write('[section]asdfasdf\nkey = value')
        result = mon.keyring_parser(keyring.strpath)

        assert result == []


class TestConcatenateKeyrings(object):

    def setup(self):
        self.args = Mock()

    def make_keyring(self, tmpdir, name, contents):
        keyring = tmpdir.join(name)
        keyring.write(contents)
        return keyring

    def test_multiple_keyrings_work(self, tmpdir):
        self.make_keyring(tmpdir, 'foo.keyring', '[mon.1]\nkey = value\n')
        self.make_keyring(tmpdir, 'bar.keyring', '[mon.2]\nkey = value\n')
        self.make_keyring(tmpdir, 'fez.keyring', '[mon.3]\nkey = value\n')
        self.args.keyrings = tmpdir.strpath
        result = mon.concatenate_keyrings(self.args).split('\n')
        assert '[mon.2]' in result
        assert 'key = value' in result
        assert '[mon.3]' in result
        assert 'key = value' in result
        assert '[mon.1]' in result
        assert 'key = value' in result

    def test_skips_duplicate_content(self, tmpdir):
        self.make_keyring(tmpdir, 'foo.keyring', '[mon.1]\nkey = value\n')
        self.make_keyring(tmpdir, 'bar.keyring', '[mon.2]\nkey = value\n')
        self.make_keyring(tmpdir, 'fez.keyring', '[mon.3]\nkey = value\n')
        self.make_keyring(tmpdir, 'dupe.keyring', '[mon.3]\nkey = value\n')
        self.args.keyrings = tmpdir.strpath
        result = mon.concatenate_keyrings(self.args).split('\n')
        assert result.count('[mon.3]') == 1
        assert result.count('[mon.2]') == 1
        assert result.count('[mon.1]') == 1

    def test_errors_when_no_keyrings(self, tmpdir):
        self.args.keyrings = tmpdir.strpath

        with py.test.raises(RuntimeError):
            mon.concatenate_keyrings(self.args)
