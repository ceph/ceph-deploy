from mock import patch, Mock
from ceph_deploy.util import pkg_managers


class TestRPM(object):

    def setup(self):
        self.to_patch = 'ceph_deploy.util.pkg_managers.wrappers'

    def test_extend_flags(self):
        fake_check_call = Mock()
        with patch(self.to_patch, fake_check_call):
            pkg_managers.rpm(
                Mock(),
                Mock(),
                ['-f', 'vim'])
            result = fake_check_call.check_call.call_args_list[-1]
        assert result[0][-1] == ['rpm', '-Uvh', '-f', 'vim']


