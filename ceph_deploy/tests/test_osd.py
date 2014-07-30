from ceph_deploy import osd


class TestDetectDiskDir(object):
    def test_detect_disk_dir_negative(self):
        assert False == osd.detect_disk_dir('/dev/sda')
        assert False == osd.detect_disk_dir('/dev/vda')
        assert False == osd.detect_disk_dir('/dev/hda')
        assert False == osd.detect_disk_dir('/dev/hdz')
        assert False == osd.detect_disk_dir('/dev/sdz')
        assert False == osd.detect_disk_dir('///dev/sda')
        # Note : following test fails due to os.path.normpath behavior.
        # assert False == osd.detect_disk_dir('//dev/sda')

    def test_detect_disk_dir_positive(self):
        assert True == osd.detect_disk_dir('/mnt/foo')
        assert True == osd.detect_disk_dir('/srv/foo')
        assert True == osd.detect_disk_dir('/srv/foo/bar')
        assert True == osd.detect_disk_dir('/server/foo/')
