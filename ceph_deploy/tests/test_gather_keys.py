from ceph_deploy import gatherkeys
from ceph_deploy import new
import mock
import pytest
import tempfile
import os
import shutil


def get_key_static(keytype, key_path):
    with file(key_path, 'w') as f:
        f.write("[%s]\n" % (gatherkeys.keytype_identity(keytype)))
        f.write("key=fred\n")


def get_key_dynamic(keytype, key_path):
    with open(key_path, 'w', 0600) as f:
        f.write("[%s]\n" % (gatherkeys.keytype_identity(keytype)))
        f.write("key='%s'" % (new.generate_auth_key()))


def mock_time_strftime(time_format):
    return "20160412144231"


def mock_get_keys_fail(args, host, dest_dir):
    return False


def mock_get_keys_sucess_static(args, host, dest_dir):
    for keytype in ["admin", "mon", "osd", "mds", "rgw"]:
        keypath = gatherkeys.keytype_path_to(args, keytype)
        path = "%s/%s" % (dest_dir, keypath)
        get_key_static(keytype, path)
    return True


def mock_get_keys_sucess_dynamic(args, host, dest_dir):
    for keytype in ["admin", "mon", "osd", "mds", "rgw"]:
        keypath = gatherkeys.keytype_path_to(args, keytype)
        path = "%s/%s" % (dest_dir, keypath)
        get_key_dynamic(keytype, path)
    return True


class TestGatherKeys(object):
    """
    Since we are testing things that effect the content of the current working
    directory we should test in a clean empty directory.
    """
    def setup(self):
        """
        Make temp directory for tests and set as current working directory
        """
        self.orginaldir = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)


    def teardown(self):
        """
        Set current working directory to old value
        Remove temp directory and content
        """
        os.chdir(self.orginaldir)
        shutil.rmtree(self.test_dir)


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_with_mon', mock_get_keys_fail)
    def test_gatherkeys_fail(self):
        """
        Test 'gatherkeys' fails when connecting to mon fails.
        """
        args = mock.Mock()
        args.cluster = "ceph"
        args.mon = ['host1']
        with pytest.raises(RuntimeError):
            gatherkeys.gatherkeys(args)


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_with_mon', mock_get_keys_sucess_static)
    def test_gatherkeys_success(self):
        """
        Test 'gatherkeys' succeeds when getinig keys that are always the same.
        Test 'gatherkeys' does not backup identical keys
        """
        args = mock.Mock()
        args.cluster = "ceph"
        args.mon = ['host1']
        gatherkeys.gatherkeys(args)
        dir_content = os.listdir(self.test_dir)
        assert "ceph.client.admin.keyring" in dir_content
        assert "ceph.bootstrap-mds.keyring" in dir_content
        assert "ceph.mon.keyring" in dir_content
        assert "ceph.bootstrap-osd.keyring" in dir_content
        assert "ceph.bootstrap-rgw.keyring" in dir_content
        assert len(dir_content) == 5
        # Now we repeat as no new keys are generated
        gatherkeys.gatherkeys(args)
        dir_content = os.listdir(self.test_dir)
        assert len(dir_content) == 5


    @mock.patch('ceph_deploy.gatherkeys.time.strftime', mock_time_strftime)
    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_with_mon', mock_get_keys_sucess_dynamic)
    def test_gatherkeys_backs_up(self):
        """
        Test 'gatherkeys' succeeds when getinig keys that are always different.
        Test 'gatherkeys' does backup keys that are not identical.
        """
        args = mock.Mock()
        args.cluster = "ceph"
        args.mon = ['host1']
        gatherkeys.gatherkeys(args)
        dir_content = os.listdir(self.test_dir)
        assert "ceph.client.admin.keyring" in dir_content
        assert "ceph.bootstrap-mds.keyring" in dir_content
        assert "ceph.mon.keyring" in dir_content
        assert "ceph.bootstrap-osd.keyring" in dir_content
        assert "ceph.bootstrap-rgw.keyring" in dir_content
        assert len(dir_content) == 5
        # Now we repeat as new keys are generated and old
        # are backed up
        gatherkeys.gatherkeys(args)
        dir_content = os.listdir(self.test_dir)
        mocked_time = mock_time_strftime(None)
        assert "ceph.client.admin.keyring" in dir_content
        assert "ceph.bootstrap-mds.keyring" in dir_content
        assert "ceph.mon.keyring" in dir_content
        assert "ceph.bootstrap-osd.keyring" in dir_content
        assert "ceph.bootstrap-rgw.keyring" in dir_content
        assert "ceph.client.admin.keyring-%s" % (mocked_time) in dir_content
        assert "ceph.bootstrap-mds.keyring-%s" % (mocked_time) in dir_content
        assert "ceph.mon.keyring-%s" % (mocked_time) in dir_content
        assert "ceph.bootstrap-osd.keyring-%s" % (mocked_time) in dir_content
        assert "ceph.bootstrap-rgw.keyring-%s" % (mocked_time) in dir_content
        assert len(dir_content) == 10
