from ceph_deploy.hosts import suse 
from ceph_deploy.hosts.suse.install import map_components, NON_SPLIT_PACKAGES

class TestSuseInit(object):
    def setup(self):
        self.host = suse

    def test_choose_init_default(self):
        self.host.release = None
        init_type = self.host.choose_init(self.host)
        assert init_type == "systemd"

    def test_choose_init_SLE_11(self):
        self.host.release = '11'
        init_type = self.host.choose_init(self.host)
        assert init_type == "sysvinit"

    def test_choose_init_SLE_12(self):
        self.host.release = '12'
        init_type = self.host.choose_init(self.host)
        assert init_type == "systemd"

    def test_choose_init_openSUSE_13_1(self):
        self.host.release = '13.1'
        init_type = self.host.choose_init(self.host)
        assert init_type == "systemd"

class TestSuseMapComponents(object):
    def test_valid(self):
        pkgs = map_components(NON_SPLIT_PACKAGES, ['ceph-osd', 'ceph-common', 'ceph-radosgw'])
        assert 'ceph' in pkgs
        assert 'ceph-common' in pkgs
        assert 'ceph-radosgw' in pkgs
        assert 'ceph-osd' not in pkgs
