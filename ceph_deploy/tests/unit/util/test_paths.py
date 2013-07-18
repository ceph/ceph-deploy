from ceph_deploy.util import paths


class TestMonPaths(object):

    def test_base_path(self):
        assert paths.mon._base.endswith('/ceph-')

    def test_path(self):
        result = paths.mon.path('ceph', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('/ceph-myhostname')

    def test_done(self):
        result = paths.mon.done('ceph', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('ceph-myhostname/done')

    def test_init(self):
        result = paths.mon.init('ceph', 'myhostname', 'init')
        assert result.startswith('/')
        assert result.endswith('ceph-myhostname/init')

    def test_keyring(self):
        result = paths.mon.keyring('mycluster', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('tmp/mycluster-myhostname.mon.keyring')

