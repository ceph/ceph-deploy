from ceph_deploy import osd


class TestMountPoint(object):

    def setup(self):
        self.osd_name = 'osd.1'

    def test_osd_name_not_found(self):
        output = [
            '/dev/sda :',
            ' /dev/sda1 other, ext2, mounted on /boot',
            ' /dev/sda2 other',
            ' /dev/sda5 other, LVM2_member',
        ]
        assert osd.get_osd_mount_point(output, self.osd_name) is None

    def test_osd_name_is_found(self):
        output = [
            '/dev/sda :',
            ' /dev/sda1 other, ext2, mounted on /boot',
            ' /dev/sda2 other',
            ' /dev/sda5 other, LVM2_member',
            '/dev/sdb :',
            ' /dev/sdb1 ceph data, active, cluster ceph, osd.1, journal /dev/sdb2',
        ]
        result = osd.get_osd_mount_point(output, self.osd_name)
        assert result == '/dev/sdb1'

    def test_osd_name_not_found_but_contained_in_output(self):
        output = [
            '/dev/sda :',
            ' /dev/sda1 otherosd.1, ext2, mounted on /boot',
            ' /dev/sda2 other',
            ' /dev/sda5 other, LVM2_member',
        ]
        assert osd.get_osd_mount_point(output, self.osd_name) is None
