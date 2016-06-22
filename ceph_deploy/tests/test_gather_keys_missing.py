from ceph_deploy import gatherkeys
from ceph_deploy import new
import mock
import tempfile
import shutil
import os
import pytest


class mock_conn(object):
    def __init__(self):
        pass

class mock_distro(object):
    def __init__(self):
        self.conn = mock_conn()

class mock_rlogger(object):
    def error(self, *arg):
        return

    def debug(self, *arg):
        return


def mock_remoto_process_check_success(conn, args):
    secret = new.generate_auth_key()
    out = '[mon.]\nkey = %s\ncaps mon = allow *\n' % secret
    return out.encode('utf-8').split(b'\n'), [], 0


def mock_remoto_process_check_rc_error(conn, args):
    return [b""], [b"this failed\n"], 1


class TestGatherKeysMissing(object):
    """
    Since we are testing things that effect the content a directory we should
    test in a clean empty directory.
    """

    def setup(self):
        """
        Make temp directory for tests.
        """
        self.args = mock.Mock()
        self.distro = mock_distro()
        self.test_dir = tempfile.mkdtemp()
        self.rlogger = mock_rlogger()
        self.keypath_remote = "some_path"

    def teardown(self):
        """
        Remove temp directory and content
        """
        shutil.rmtree(self.test_dir)

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    def test_success_admin(self):
        keytype = 'admin'
        rc = gatherkeys.gatherkeys_missing(
            self.args,
            self.distro,
            self.rlogger,
            self.keypath_remote,
            keytype,
            self.test_dir
            )
        assert rc is True
        keyname = gatherkeys.keytype_path_to(self.args, keytype)
        keypath_gen = os.path.join(self.test_dir, keyname)
        assert os.path.isfile(keypath_gen)

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    def test_success_mds(self):
        keytype = 'mds'
        rc = gatherkeys.gatherkeys_missing(
            self.args,
            self.distro,
            self.rlogger,
            self.keypath_remote,
            keytype,
            self.test_dir
            )
        assert rc is True
        keyname = gatherkeys.keytype_path_to(self.args, keytype)
        keypath_gen = os.path.join(self.test_dir, keyname)
        assert os.path.isfile(keypath_gen)

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    def test_success_osd(self):
        keytype = 'osd'
        rc = gatherkeys.gatherkeys_missing(
            self.args,
            self.distro,
            self.rlogger,
            self.keypath_remote,
            keytype,
            self.test_dir
            )
        assert rc is True
        keyname = gatherkeys.keytype_path_to(self.args, keytype)
        keypath_gen = os.path.join(self.test_dir, keyname)
        assert os.path.isfile(keypath_gen)

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    def test_success_rgw(self):
        keytype = 'rgw'
        rc = gatherkeys.gatherkeys_missing(
            self.args,
            self.distro,
            self.rlogger,
            self.keypath_remote,
            keytype,
            self.test_dir
            )
        assert rc is True
        keyname = gatherkeys.keytype_path_to(self.args, keytype)
        keypath_gen = os.path.join(self.test_dir, keyname)
        assert os.path.isfile(keypath_gen)

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_rc_error)
    def test_remoto_process_check_rc_error(self):
        keytype = 'admin'
        rc = gatherkeys.gatherkeys_missing(
            self.args,
            self.distro,
            self.rlogger,
            self.keypath_remote,
            keytype,
            self.test_dir
            )
        assert rc is False
        keyname = gatherkeys.keytype_path_to(self.args, keytype)
        keypath_gen = os.path.join(self.test_dir, keyname)
        assert not os.path.isfile(keypath_gen)

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    def test_fail_identity_missing(self):
        keytype = 'silly'
        with pytest.raises(RuntimeError):
            gatherkeys.gatherkeys_missing(
                self.args,
                self.distro,
                self.rlogger,
                self.keypath_remote,
                keytype,
                self.test_dir
                )

    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    def test_fail_capabilities_missing(self):
        keytype = 'mon'
        with pytest.raises(RuntimeError):
            gatherkeys.gatherkeys_missing(
                self.args,
                self.distro,
                self.rlogger,
                self.keypath_remote,
                keytype,
                self.test_dir
                )

