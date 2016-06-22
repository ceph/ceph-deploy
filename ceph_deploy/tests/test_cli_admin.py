import os
import subprocess

import pytest
from mock import patch, MagicMock, Mock

from ceph_deploy.cli import _main as main
from ceph_deploy.hosts import remotes
from ceph_deploy.tests.directory import directory


def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'admin', 'host1'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read().decode('utf-8')
    assert 'No such file or directory: \'ceph.conf\'' in result
    assert err.value.status == 1


def test_bad_no_key(tmpdir, cli):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'admin', 'host1'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read().decode('utf-8')
    assert 'ceph.client.admin.keyring not found' in result
    assert err.value.status == 1


def test_write_keyring(tmpdir):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with tmpdir.join('ceph.client.admin.keyring').open('wb'):
        pass

    etc_ceph = os.path.join(str(tmpdir), 'etc', 'ceph')
    os.makedirs(etc_ceph)

    distro = MagicMock()
    distro.conn = MagicMock()
    remotes.write_file.__defaults__ = (0o644, str(tmpdir), -1, -1)
    distro.conn.remote_module = remotes
    distro.conn.remote_module.write_conf = Mock()

    with patch('ceph_deploy.admin.hosts'):
        with patch('ceph_deploy.admin.hosts.get', MagicMock(return_value=distro)):
            with directory(str(tmpdir)):
                main(args=['admin', 'host1'])

    keyring_file = os.path.join(etc_ceph, 'ceph.client.admin.keyring')
    assert os.path.exists(keyring_file)

    file_mode = oct(os.stat(keyring_file).st_mode & 0o777)
    assert file_mode == oct(0o600)
