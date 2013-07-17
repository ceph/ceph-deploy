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


    try:
        with directory(str(tmpdir)):
            main(
                args=['-v', 'install', 'storehost1'],
                namespace=ns,
                )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)

    ns.pushy.assert_has_calls([
            mock.call('ssh+sudo:storehost1'),
        ])

    call_list = conn.compile.call_args_list
    mock.call(install.lsb.check_lsb_release) == call_list[0]
    mock.call(install.lsb.lsb_release) == call_list[1]
    mock.call(install.install_debian) == call_list[2]
    assert len(call_list) == 3
