from ceph_deploy.hosts.alt.install import map_components, NON_SPLIT_PACKAGES


class TestALTMapComponents(object):
    def test_valid(self):
        pkgs = map_components(NON_SPLIT_PACKAGES, ['ceph-osd', 'ceph-common', 'ceph-radosgw'])
        assert 'ceph' in pkgs
        assert 'ceph-common' in pkgs
        assert 'ceph-radosgw' in pkgs
        assert 'ceph-osd' not in pkgs
