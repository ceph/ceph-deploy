from mock import Mock

from ceph_deploy import install


class TestSanitizeArgs(object):

    def setup(self):
        self.args = Mock()
        # set the default behavior we set in cli.py
        self.args.default_release = False

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
