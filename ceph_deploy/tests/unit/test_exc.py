from pytest import raises
from ceph_deploy import exc


class TestExecutableNotFound(object):

    def test_executable_is_used(self):
        with raises(exc.DeployError) as error:
            raise exc.ExecutableNotFound('vim', 'node1')
        assert "'vim'" in str(error)

    def test_host_is_used(self):
        with raises(exc.DeployError) as error:
            raise exc.ExecutableNotFound('vim', 'node1')
        assert "node1" in str(error)

