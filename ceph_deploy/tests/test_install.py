from mock import Mock

from ceph_deploy import install


class TestSanitizeArgs(object):

    def setup(self):
        self.args = Mock()
        # set the default behavior we set in cli.py
        self.args.default_release = False
        self.args.stable = None

    def test_args_release_not_specified(self):
        self.args.release = None
        result = install.sanitize_args(self.args)
        # XXX
        # we should get `args.release` to be the latest release
        # but we don't want to be updating this test every single
        # time there is a new default value, and we can't programatically
        # change that. Future improvement: make the default release a
        # variable in `ceph_deploy/__init__.py`
        assert result.default_release is True

    def test_args_release_is_specified(self):
        self.args.release = 'dumpling'
        result = install.sanitize_args(self.args)
        assert result.default_release is False

    def test_args_release_stable_is_used(self):
        self.args.stable = 'dumpling'
        result = install.sanitize_args(self.args)
        assert result.release == 'dumpling'

    def test_args_stable_is_not_used(self):
        self.args.release = 'dumpling'
        result = install.sanitize_args(self.args)
        assert result.stable is None


class TestDetectComponents(object):

    def setup(self):
        self.args = Mock()
        # default values for install_* flags
        self.args.install_all = False
        self.args.install_mds = False
        self.args.install_mon = False
        self.args.install_osd = False
        self.args.install_rgw = False
        self.args.install_tests = False
        self.args.install_common = False
        self.args.repo = False
        self.distro = Mock()

    def test_install_with_repo_option_returns_no_packages(self):
        self.args.repo = True
        result = install.detect_components(self.args, self.distro)
        assert result == []

    def test_install_all_returns_all_packages_deb(self):
        self.args.install_all = True
        self.distro.is_rpm = False
        self.distro.is_deb = True
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted([
            'ceph-osd', 'ceph-mds', 'ceph-mon', 'radosgw'
        ])

    def test_install_all_with_other_options_returns_all_packages_deb(self):
        self.distro.is_rpm = False
        self.distro.is_deb = True
        self.args.install_all = True
        self.args.install_mds = True
        self.args.install_mon = True
        self.args.install_osd = True
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted([
            'ceph-osd', 'ceph-mds', 'ceph-mon', 'radosgw'
        ])

    def test_install_all_returns_all_packages_rpm(self):
        self.args.install_all = True
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted([
            'ceph-osd', 'ceph-mds', 'ceph-mon', 'ceph-radosgw'
        ])

    def test_install_all_with_other_options_returns_all_packages_rpm(self):
        self.args.install_all = True
        self.args.install_mds = True
        self.args.install_mon = True
        self.args.install_osd = True
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted([
            'ceph-osd', 'ceph-mds', 'ceph-mon', 'ceph-radosgw'
        ])

    def test_install_only_one_component(self):
        self.args.install_osd = True
        result = install.detect_components(self.args, self.distro)
        assert result == ['ceph-osd']

    def test_install_a_couple_of_components(self):
        self.args.install_osd = True
        self.args.install_mds = True
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted(['ceph-osd', 'ceph-mds'])

    def test_install_tests(self):
        self.args.install_tests = True
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted(['ceph-test'])

    def test_install_all_should_be_default_when_no_options_passed(self):
        result = sorted(install.detect_components(self.args, self.distro))
        assert result == sorted([
            'ceph-osd', 'ceph-mds', 'ceph-mon', 'ceph-radosgw'
        ])
