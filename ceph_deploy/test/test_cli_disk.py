import argparse
import collections
import mock
import pytest
import subprocess

from ..cli import main
from .. import disk

from .directory import directory


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'disk', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        got = p.stdout.read()
        assert got == """\
usage: ceph-deploy disk [-h] HOST:DISK [HOST:DISK ...]

Prepare a data disk on remote host.

positional arguments:
  HOST:DISK   host and disk to prepare

optional arguments:
  -h, --help  show this help message and exit
"""


def test_bad_no_disk(tmpdir, cli):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'disk'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy disk [-h] HOST:DISK [HOST:DISK ...]
ceph-deploy disk: error: too few arguments
"""

    assert err.value.status == 2


def test_simple(tmpdir):
    with tmpdir.join('ceph.conf').open('w') as f:
        f.write("""\
[global]
fsid = 6ede5564-3cf1-44b5-aa96-1c77b0c3e1d0
mon host = host1
""")

    ns = argparse.Namespace()

    conn = mock.NonCallableMock(name='PushyClient')
    mock_compiled = collections.defaultdict(mock.Mock)
    conn.compile.side_effect = mock_compiled.__getitem__

    ns.pushy = mock.Mock()
    ns.pushy.return_value = conn

    try:
        with directory(str(tmpdir)):
            main(
                args=['-v', 'disk', 'storehost1:sdc'],
                namespace=ns,
                )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)

    ns.pushy.assert_called_once_with('ssh+sudo:storehost1')

    mock_compiled.pop(disk.prepare_disk).assert_called_once_with(
        cluster='ceph',
        disk='/dev/sdc',
        )

    assert mock_compiled == {}
