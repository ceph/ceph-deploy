from mock import MagicMock, call

from ceph_deploy.util import init_systems


class TestSysV(object):

    def setup(self):
        self.init = init_systems.SysV(MagicMock())
        self.init._run = MagicMock()

    def test_name(self):
        assert self.init.name == "sysvinit"

    def test_start_mon(self):
        self.init._service_exe = "service"
        self.init.start("ceph-mon", name="test")
        self.init._run.assert_called_once_with([
            'service',
            'ceph',
            '-c',
            '/etc/ceph/ceph.conf',
            'start',
            'mon.test'
        ])

    def test_start_mds(self):
        self.init._service_exe = "service"
        self.init.start("ceph-mds", name="test")
        self.init._run.assert_called_once_with([
            'service',
            'ceph',
            '-c',
            '/etc/ceph/ceph.conf',
            'start',
            'mds.test'
        ])

    def test_start_rgw(self):
        self.init._service_exe = "service"
        self.init.start("ceph-radosgw", name="test")
        self.init._run.assert_called_once_with([
            'service',
            'ceph-radosgw',
            'start',
        ])

    def test_enable_mon(self):
        self.init.enable("ceph-mon")
        self.init._run.assert_called_once_with([
            'chkconfig',
            'ceph',
            'on',
        ])

    def test_enable_mon_ignores_extra_args(self):
        self.init.enable("ceph-mon", cluster="test", name="test")
        self.init._run.assert_called_once_with([
            'chkconfig',
            'ceph',
            'on',
        ])

    def test_enable_osd(self):
        self.init.enable("ceph-osd")
        self.init._run.assert_called_once_with([
            'chkconfig',
            'ceph',
            'on',
        ])

    def test_enable_mds(self):
        self.init.enable("ceph-mds")
        self.init._run.assert_called_once_with([
            'chkconfig',
            'ceph',
            'on',
        ])

    def test_enable_rgw(self):
        self.init.enable("ceph-radosgw")
        self.init._run.assert_called_once_with([
            'chkconfig',
            'ceph-radosgw',
            'on',
        ])


class TestUpstart(object):

    def setup(self):
        self.init = init_systems.Upstart(MagicMock())
        self.init._run = MagicMock()

    def test_name(self):
        assert self.init.name == "upstart"

    def test_start_mon(self):
        self.init.start("ceph-mon", name="test")
        self.init._run.assert_called_once_with([
            'initctl',
            'emit',
            'ceph-mon',
            'cluster=ceph',
            'id=test'
        ])

    def test_start_mds(self):
        self.init.start("ceph-mds", name="test")
        self.init._run.assert_called_once_with([
            'initctl',
            'emit',
            'ceph-mds',
            'cluster=ceph',
            'id=test'
        ])

    def test_start_rgw(self):
        self.init.start("ceph-radosgw", name="test")
        self.init._run.assert_called_once_with([
            'initctl',
            'emit',
            'radosgw',
            'cluster=ceph',
            'id=test'
        ])

    def test_enable_mon(self):
        self.init.enable("ceph-mon")
        self.init._run.assert_not_called()

    def test_enable_osd(self):
        self.init.enable("ceph-mon")
        self.init._run.assert_not_called()

    def test_enable_mds(self):
        self.init.enable("ceph-mon")
        self.init._run.assert_not_called()

    def test_enable_rgw(self):
        self.init.enable("ceph-mon")
        self.init._run.assert_not_called()


class TestSystemD(object):

    def setup(self):
        self.init = init_systems.SystemD(MagicMock())
        self.init._run = MagicMock()

    def test_name(self):
        assert self.init.name == "systemd"

    def test_start_mon(self):
        self.init.start("ceph-mon", name="test")
        self.init._run.assert_called_once_with([
            'systemctl',
            'start',
            'ceph-mon@test',
        ])

    def test_start_mds(self):
        self.init.start("ceph-mds", name="test")
        self.init._run.assert_called_once_with([
            'systemctl',
            'start',
            'ceph-mds@test',
        ])

    def test_start_rgw(self):
        self.init.start("ceph-radosgw", name="test")
        self.init._run.assert_called_once_with([
            'systemctl',
            'start',
            'ceph-radosgw@test',
        ])

    def test_enable_mon(self):
        self.init.enable("ceph-mon", name="test")
        calls = [
            call([
                'systemctl',
                'enable',
                'ceph-mon@test',
            ]),
            call([
                'systemctl',
                'enable',
                'ceph.target',
            ])
        ]
        self.init._run.assert_has_calls(calls, any_order=True)

    def test_enable_osd(self):
        self.init.enable("ceph-osd", name="test")
        self.init._run.assert_called_once_with([
            'systemctl',
            'enable',
            'ceph.target',
        ])

    def test_enable_mds(self):
        self.init.enable("ceph-mds", name="test")
        calls = [
            call([
                'systemctl',
                'enable',
                'ceph-mds@test',
            ]),
            call([
                'systemctl',
                'enable',
                'ceph.target',
            ])
        ]
        self.init._run.assert_has_calls(calls, any_order=True)

    def test_enable_rgw(self):
        self.init.enable("ceph-radosgw", name="test")
        calls = [
            call([
                'systemctl',
                'enable',
                'ceph-radosgw@test',
            ]),
            call([
                'systemctl',
                'enable',
                'ceph.target',
            ])
        ]
        self.init._run.assert_has_calls(calls, any_order=True)
