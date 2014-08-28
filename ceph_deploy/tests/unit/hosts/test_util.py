from ceph_deploy.hosts import util
from mock import Mock


class TestInstallYumPriorities(object):

    def setup(self):
        self.distro = Mock()
        self.patch_path = 'ceph_deploy.hosts.centos.install.pkg_managers.yum'
        self.yum = Mock()

    def test_centos_six(self):
        self.distro.release = ('6', '0')
        self.distro.normalized_name = 'centos'
        util.install_yum_priorities(self.distro, _yum=self.yum)
        assert self.yum.call_args[0][1] == 'yum-plugin-priorities'

    def test_centos_five(self):
        self.distro.release = ('5', '0')
        self.distro.normalized_name = 'centos'
        util.install_yum_priorities(self.distro, _yum=self.yum)
        assert self.yum.call_args[0][1] == 'yum-priorities'

    def test_fedora(self):
        self.distro.release = ('20', '0')
        self.distro.normalized_name = 'fedora'
        util.install_yum_priorities(self.distro, _yum=self.yum)
        assert self.yum.call_args[0][1] == 'yum-plugin-priorities'

