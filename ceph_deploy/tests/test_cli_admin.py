import pytest
import subprocess


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'admin', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
    assert 'usage: ceph-deploy admin' in result
    assert 'positional arguments' in result
    assert 'optional arguments' in result


def test_bad_no_hosts(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'admin'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
    assert 'usage: ceph-deploy admin' in result
    assert 'too few arguments' in result
    assert err.value.status == 2


def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'admin', 'host1'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
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
            result = p.stderr.read()
    assert 'ceph.client.admin.keyring not found' in result
    assert err.value.status == 1
