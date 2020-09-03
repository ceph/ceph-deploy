try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from textwrap import dedent
import pytest
from mock import Mock, patch, mock_open
from ceph_deploy import conf


class TestLocateOrCreate(object):

    def setup(self):
        self.fake_file = mock_open()

    def test_no_conf(self):
        fake_path = Mock()
        fake_path.exists = Mock(return_value=False)
        with patch('ceph_deploy.conf.cephdeploy.open', self.fake_file, create=True):
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
        cfg.read_file(conf_file)
        assert cfg.get_list('foo', 'key') == ['']

    def test_get_list_empty_when_no_key(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        """))
        cfg.read_file(conf_file)
        assert cfg.get_list('foo', 'key') == []

    def test_get_list_if_value_is_one_item(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1
        """))
        cfg.read_file(conf_file)
        assert cfg.get_list('foo', 'key') == ['1']

    def test_get_list_with_mutltiple_items(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1, 3, 4
        """))
        cfg.read_file(conf_file)
        assert cfg.get_list('foo', 'key') == ['1', '3', '4']

    def test_get_rid_of_comments(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1, 3, 4 # this is a wonderful comment y'all
        """))
        cfg.read_file(conf_file)
        assert cfg.get_list('foo', 'key') == ['1', '3', '4']

    def test_get_rid_of_whitespace(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        key = 1,   3     ,        4
        """))
        cfg.read_file(conf_file)
        assert cfg.get_list('foo', 'key') == ['1', '3', '4']

    def test_get_default_repo(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        default = True
        """))
        cfg.read_file(conf_file)
        assert cfg.get_default_repo() == 'foo'

    def test_get_default_repo_fails_non_truthy(self):
        cfg = conf.cephdeploy.Conf()
        conf_file = StringIO(dedent("""
        [foo]
        default = 0
        """))
        cfg.read_file(conf_file)
        assert cfg.get_default_repo() is False


truthy_values = ['yes', 'true', 'on']
falsy_values = ['no', 'false', 'off']


class TestSetOverrides(object):

    def setup(self):
        self.args = Mock()
        self.args.func.__name__ = 'foo'
        self.conf = Mock()

    def test_override_global(self):
        self.conf.sections = Mock(return_value=['ceph-deploy-global'])
        self.conf.items = Mock(return_value=(('foo', 1),))
        arg_obj = conf.cephdeploy.set_overrides(self.args, self.conf)
        assert arg_obj.foo == 1

    def test_override_foo_section(self):
        self.conf.sections = Mock(
            return_value=['ceph-deploy-global', 'ceph-deploy-foo']
        )
        self.conf.items = Mock(return_value=(('bar', 1),))
        arg_obj = conf.cephdeploy.set_overrides(self.args, self.conf)
        assert arg_obj.bar == 1

    @pytest.mark.parametrize('value', truthy_values)
    def test_override_truthy_values(self, value):
        self.conf.sections = Mock(
            return_value=['ceph-deploy-global', 'ceph-deploy-install']
        )
        self.conf.items = Mock(return_value=(('bar', value),))
        arg_obj = conf.cephdeploy.set_overrides(self.args, self.conf)
        assert arg_obj.bar is True

    @pytest.mark.parametrize('value', falsy_values)
    def test_override_falsy_values(self, value):
        self.conf.sections = Mock(
            return_value=['ceph-deploy-global', 'ceph-deploy-install']
        )
        self.conf.items = Mock(return_value=(('bar', value),))
        arg_obj = conf.cephdeploy.set_overrides(self.args, self.conf)
        assert arg_obj.bar is False
