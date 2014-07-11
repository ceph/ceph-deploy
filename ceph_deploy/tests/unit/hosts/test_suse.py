from ceph_deploy.hosts import suse 

class TestSuseInit(object):
    def setup(self):
        self.host = suse

    def test_choose_init_default(self):
        self.host.release = None
        init_type = self.host.choose_init()
        assert ( init_type == "sysvinit")
        
    def test_choose_init_SLE_11(self):
        self.host.release = '11'
        init_type = self.host.choose_init()
        assert ( init_type == "sysvinit")

    def test_choose_init_SLE_12(self):
        self.host.release = '12'
        init_type = self.host.choose_init()
        assert ( init_type == "systemd")

    def test_choose_init_openSUSE_13_1(self):
        self.host.release = '13.1'
        init_type = self.host.choose_init()
        assert ( init_type == "systemd")
