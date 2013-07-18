from ceph_deploy.util import constants


class TestPaths(object):

    def test_mon_path(self):
        assert constants.mon_path.startswith('/')
        assert constants.mon_path.endswith('/mon')

    def test_mds_path(self):
        assert constants.mds_path.startswith('/')
        assert constants.mds_path.endswith('/mds')
