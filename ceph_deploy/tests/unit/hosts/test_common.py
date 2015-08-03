from ceph_deploy.hosts.common import map_components


class TestMapComponents(object):

    def test_map_components_all_split(self):
        components = ['ceph-mon', 'ceph-osd']
        packages = map_components([], components)
        assert set(packages) == set(components)

    def test_map_components_mds_not_split(self):
        components = ['ceph-mon', 'ceph-osd', 'ceph-mds']
        packages = map_components(['ceph-mds'], components)
        assert set(packages) == set(['ceph-mon', 'ceph-osd', 'ceph'])

    def test_map_components_no_duplicates(self):
        components = ['ceph-mon', 'ceph-osd', 'ceph-mds']
        packages = map_components(['ceph-mds', 'ceph-osd'], components)
        assert set(packages) == set(['ceph-mon', 'ceph'])
        assert len(packages) == len(set(['ceph-mon', 'ceph']))

    def test_map_components_no_components(self):
        packages = map_components(['ceph-mon'], [])
        assert len(packages) == 0
