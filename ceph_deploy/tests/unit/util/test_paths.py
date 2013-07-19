from ceph_deploy.util import paths


class TestMonPaths(object):

    def test_base_path(self):
        result = paths.mon.base('mycluster')
        assert result.endswith('/mycluster-')

    def test_path(self):
        result = paths.mon.path('mycluster', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('/mycluster-myhostname')

    def test_done(self):
        result = paths.mon.done('mycluster', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('mycluster-myhostname/done')

    def test_init(self):
        result = paths.mon.init('mycluster', 'myhostname', 'init')
        assert result.startswith('/')
        assert result.endswith('mycluster-myhostname/init')

    def test_keyring(self):
        result = paths.mon.keyring('mycluster', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('tmp/mycluster-myhostname.mon.keyring')

