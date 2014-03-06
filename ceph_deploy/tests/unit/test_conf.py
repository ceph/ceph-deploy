from mock import Mock, patch
from ceph_deploy import conf
from ceph_deploy.tests import fakes


class TestLocateOrCreate(object):

    def setup(self):
        self.fake_write = Mock(name='fake_write')
        self.fake_file = fakes.mock_open(data=self.fake_write)
        self.fake_file.readline.return_value = self.fake_file

    def test_no_conf(self):
        with patch('__builtin__.open', self.fake_file):
            conf.cephdeploy.location()

        assert self.fake_file.called is True
        assert self.fake_file.call_args[0][0].endswith('/.cephdeploy.conf')

    def test_cwd_conf_exists(self):
        fake_path = Mock()
        fake_path.join = Mock(return_value='/srv/cephdeploy.conf')
        fake_path.exists = Mock(return_value=True)
        with patch('ceph_deploy.conf.cephdeploy.path', fake_path):
            result = conf.cephdeploy.location()

        assert result == '/srv/cephdeploy.conf'

    def test_home_conf_exists(self):
        fake_path = Mock()
        fake_path.expanduser = Mock(return_value='/home/alfredo/.cephdeploy.conf')
        fake_path.exists = Mock(side_effect=[False, True])
        with patch('ceph_deploy.conf.cephdeploy.path', fake_path):
            result = conf.cephdeploy.location()

        assert result == '/home/alfredo/.cephdeploy.conf'
