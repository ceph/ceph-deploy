from mock import Mock
import string
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


class TestOsdPerHostCheck(object):

    def setup(self):
        self.args = Mock()
        self.args.disk = [
            ('node1', '/dev/sdb'),
            ('node2', '/dev/sdb'),
            ('node3', '/dev/sdb'),
        ]
        self.disks = ['/dev/sd%s' % disk for disk in list(string.ascii_lowercase)]

    def test_no_journal_works(self):
        assert osd.exceeds_max_osds(self.args) == {}

    def test_mixed_journal_and_no_journal_works(self):
        self.args.disk = [
            ('node1', '/dev/sdb'),
            ('node2', '/dev/sdb', '/dev/sdc'),
            ('node3', '/dev/sdb'),
        ]
        assert osd.exceeds_max_osds(self.args) == {}

    def test_minimum_count_passes(self):
        self.args.disk = [
            ('node1', '/dev/sdb'),
            ('node2', '/dev/sdb'),
            ('node3', '/dev/sdb'),
        ]
        assert osd.exceeds_max_osds(self.args) == {}

    def test_exceeds_reasonable(self):
        self.args.disk = [('node1', disk) for disk in self.disks]
        assert osd.exceeds_max_osds(self.args) == {'node1': 26}
