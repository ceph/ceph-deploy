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

    def test_asok(self):
        result = paths.mon.asok('mycluster', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('mycluster-mon.myhostname.asok')

    def test_monmap(self):
        result = paths.mon.monmap('mycluster', 'myhostname')
        assert result.startswith('/')
        assert result.endswith('tmp/mycluster.myhostname.monmap')

    def test_gpg_url_release(self):
        result = paths.gpg.url('release')
        assert result == "https://download.ceph.com/keys/release.asc"

    def test_gpg_url_autobuild(self):
        result = paths.gpg.url('autobuild')
        assert result == "https://download.ceph.com/keys/autobuild.asc"

    def test_gpg_url_http(self):
        result = paths.gpg.url('release', protocol="http")
        assert result == "http://download.ceph.com/keys/release.asc"
