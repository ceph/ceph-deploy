import pytest
from ceph_deploy import calamari


class TestDistroIsSupported(object):

    @pytest.mark.parametrize(
        "distro_name",
        ['centos', 'redhat', 'ubuntu', 'debian'])
    def test_distro_is_supported(self, distro_name):
        assert calamari.distro_is_supported(distro_name) is True

    @pytest.mark.parametrize(
        "distro_name",
        ['fedora', 'mandriva', 'darwin', 'windows'])
    def test_distro_is_not_supported(self, distro_name):
        assert calamari.distro_is_supported(distro_name) is False
