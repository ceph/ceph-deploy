import argparse
import collections
import mock
import pytest
import subprocess

from ..cli import main
from .. import install

from .directory import directory


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


def test_simple(tmpdir):
    ns = argparse.Namespace()
    ns.pushy = mock.Mock()
    conn = mock.NonCallableMock(name='PushyClient')
    ns.pushy.return_value = conn

    mock_compiled = collections.defaultdict(mock.Mock)
    conn.compile.return_value = mock.Mock(return_value = ('Ubuntu', 'precise','cuttlefish'))
    fake_get_release = mock.Mock(return_value = ('Ubuntu', 'precise','cuttlefish'))
    fake_distro = mock.Mock(name='FakeDistro')
    fake_distro.return_value = fake_distro

    try:
        with directory(str(tmpdir)):
            with mock.patch('ceph_deploy.hosts.lsb.get_lsb_release', fake_get_release):
                with mock.patch('ceph_deploy.hosts.pushy', ns.pushy):
                    with mock.patch('ceph_deploy.hosts._get_distro', fake_distro):

                        main(
                            args=['-v', 'install', 'storehost1'],
                            namespace=ns,
                            )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)

    connect_calls = ns.pushy.connect.call_args[0][0]
    assert connect_calls == 'ssh+sudo:storehost1'
    assert fake_distro.name == 'Ubuntu'
    assert fake_distro.release == 'precise'
    assert fake_distro.codename == 'cuttlefish'
