from ceph_deploy import gatherkeys
from ceph_deploy import new
import tempfile
import shutil
import pytest


def write_key_mon_with_caps(path, secret):
    mon_keyring = '[mon.]\nkey = %s\ncaps mon = allow *\n' % secret
    with open(path, 'w', 0600) as f:
        f.write(mon_keyring)


def write_key_mon_with_caps_with_tab(path, secret):
    mon_keyring = '[mon.]\n\tkey = %s\n\tcaps mon = allow *\n' % secret
    with open(path, 'w', 0600) as f:
        f.write(mon_keyring)


def write_key_mon_with_caps_with_tab_quote(path, secret):
    mon_keyring = '[mon.]\n\tkey = %s\n\tcaps mon = "allow *"\n' % secret
    with open(path, 'w', 0600) as f:
        f.write(mon_keyring)


def write_key_mon_without_caps(path, secret):
    mon_keyring = '[mon.]\nkey = %s\n' % secret
    with open(path, 'w', 0600) as f:
        f.write(mon_keyring)


class TestKeysEquivalent(object):
    """
    Since we are testing things that effect the content of the current working
    directory we should test in a clean empty directory.
    """
    def setup(self):
        """
        Make temp directory for tests.
        """
        self.test_dir = tempfile.mkdtemp()


    def teardown(self):
        """
        Remove temp directory and content
        """
        shutil.rmtree(self.test_dir)


    def test_identical_with_caps(self):
        secret_01 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps(key_path_01, secret_01)
        write_key_mon_with_caps(key_path_02, secret_01)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is True


    def test_different_with_caps(self):
        secret_01 = new.generate_auth_key()
        secret_02 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps(key_path_01, secret_01)
        write_key_mon_with_caps(key_path_02, secret_02)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is False


    def test_identical_without_caps(self):
        secret_01 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_without_caps(key_path_01, secret_01)
        write_key_mon_without_caps(key_path_02, secret_01)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is True


    def test_different_without_caps(self):
        secret_01 = new.generate_auth_key()
        secret_02 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_without_caps(key_path_01, secret_01)
        write_key_mon_without_caps(key_path_02, secret_02)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is False


    def test_identical_mixed_caps(self):
        secret_01 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps(key_path_01, secret_01)
        write_key_mon_without_caps(key_path_02, secret_01)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is True


    def test_different_mixed_caps(self):
        secret_01 = new.generate_auth_key()
        secret_02 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps(key_path_01, secret_01)
        write_key_mon_without_caps(key_path_02, secret_02)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is False


    def test_identical_caps_mixed_tabs(self):
        secret_01 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps(key_path_01, secret_01)
        write_key_mon_with_caps_with_tab(key_path_02, secret_01)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is True


    def test_different_caps_mixed_tabs(self):
        secret_01 = new.generate_auth_key()
        secret_02 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps(key_path_01, secret_01)
        write_key_mon_with_caps_with_tab(key_path_02, secret_02)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is False


    def test_identical_caps_mixed_quote(self):
        secret_01 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps_with_tab(key_path_01, secret_01)
        write_key_mon_with_caps_with_tab_quote(key_path_02, secret_01)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is True


    def test_different_caps_mixed_quote(self):
        secret_01 = new.generate_auth_key()
        secret_02 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps_with_tab(key_path_01, secret_01)
        write_key_mon_with_caps_with_tab_quote(key_path_02, secret_02)
        same = gatherkeys._keyring_equivalent(key_path_01, key_path_02)
        assert same is False


    def test_missing_key_1(self):
        secret_02 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps_with_tab_quote(key_path_02, secret_02)
        with pytest.raises(IOError):
            gatherkeys._keyring_equivalent(key_path_01, key_path_02)


    def test_missing_key_2(self):
        secret_01 = new.generate_auth_key()
        key_path_01 = self.test_dir + "/01.keyring"
        key_path_02 = self.test_dir + "/02.keyring"
        write_key_mon_with_caps_with_tab_quote(key_path_01, secret_01)
        with pytest.raises(IOError):
            gatherkeys._keyring_equivalent(key_path_01, key_path_02)
