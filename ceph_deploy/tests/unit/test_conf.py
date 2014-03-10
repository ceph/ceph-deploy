from cStringIO import StringIO
from textwrap import dedent
from mock import Mock, patch
from ceph_deploy import conf
from ceph_deploy.tests import fakes


class TestLocateOrCreate(object):

    def setup(self):
        self.fake_write = Mock(name='fake_write')
        self.fake_file = fakes.mock_open(data=self.fake_write)
        self.fake_file.readline.return_value = self.fake_file

    def test_no_conf(self):
        fake_path = Mock()
        fake_path.exists = Mock(return_value=False)
        with patch('__builtin__.open', self.fake_file):
            with patch('ceph_deploy.conf.cephdeploy.path', fake_path):
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


class TestConf(object):

    def test_has_repos(self):
        cfg = conf.cephdeploy.Conf()
        cfg.sections = lambda: ['foo']
        assert cfg.has_repos is True

    def test_has_no_repos(self):
        cfg = conf.cephdeploy.Conf()
        cfg.sections = lambda: ['ceph-deploy-install']
        assert cfg.has_repos is False

    def test_get_repos_is_empty(self):
        cfg = conf.cephdeploy.Conf()
        cfg.sections = lambda: ['ceph-deploy-install']
        assert cfg.get_repos() == []

    def test_get_repos_is_not_empty(self):
        cfg = conf.cephdeploy.Conf()
        cfg.sections = lambda: ['ceph-deploy-install', 'foo']
        assert cfg.get_repos() == ['foo']

    def test_get_safe_not_empty(self):
        cfg = conf.cephdeploy.Conf()
        cfg.get = lambda section, key: True
        assert cfg.get_safe(1, 2) is True

    def test_get_safe_empty(self):
        cfg = conf.cephdeploy.Conf()
        assert cfg.get_safe(1, 2) is None


class TestConfGetList(object):

    def test_get_list_empty(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key =
        """))
        cfg.readfp(conf_file)
        assert cfg.get_list('foo', 'key') == ['']

    def test_get_list_empty_when_no_key(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        """))
        cfg.readfp(conf_file)
        assert cfg.get_list('foo', 'key') == []

    def test_get_list_if_value_is_one_item(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1
        """))
        cfg.readfp(conf_file)
        assert cfg.get_list('foo', 'key') == ['1']

    def test_get_list_with_mutltiple_items(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1, 3, 4
        """))
        cfg.readfp(conf_file)
        assert cfg.get_list('foo', 'key') == ['1', '3', '4']

    def test_get_rid_of_comments(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1, 3, 4 # this is a wonderful comment y'all
        """))
        cfg.readfp(conf_file)
        assert cfg.get_list('foo', 'key') == ['1', '3', '4']

    def test_get_rid_of_whitespace(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1,   3     ,        4
        """))
        cfg.readfp(conf_file)
        assert cfg.get_list('foo', 'key') == ['1', '3', '4']
