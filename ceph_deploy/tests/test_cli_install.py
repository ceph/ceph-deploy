import pytest
import subprocess


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'install', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
    assert 'usage: ceph-deploy' in result
    assert 'positional arguments:' in result
    assert 'optional arguments:' in result


def test_bad_no_host(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'install'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
    assert 'usage: ceph-deploy install' in result
    assert 'too few arguments' in result
    assert err.value.status == 2
