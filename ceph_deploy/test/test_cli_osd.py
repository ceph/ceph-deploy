import argparse
import collections
import mock
import pytest
import subprocess

from ..cli import main
from .. import osd

from .directory import directory


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'osd', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        got = p.stdout.read()
        assert got == """\
usage: ceph-deploy osd [-h] HOST [HOST ...]

Deploy ceph osd on remote hosts.

positional arguments:
  HOST        host to deploy on

optional arguments:
  -h, --help  show this help message and exit
"""


def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'osd', 'fakehost'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
ceph-deploy: Cannot load config: [Errno 2] No such file or directory: 'ceph.conf'
"""

    assert err.value.status == 1


def test_bad_no_osd(tmpdir, cli):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'osd'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy osd [-h] HOST [HOST ...]
ceph-deploy osd: error: too few arguments
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
    ns.pushy = mock.Mock()
    conn = mock.NonCallableMock(name='PushyClient')
    ns.pushy.return_value = conn

    mock_compiled = collections.defaultdict(mock.Mock)
    conn.compile.side_effect = mock_compiled.__getitem__

    BOOTSTRAP_KEY = 'fakekeyring'

    mock_compiled[osd.get_bootstrap_osd_key].return_value = BOOTSTRAP_KEY

    def _create_osd(cluster, find_key):
        key = find_key()
        assert key == BOOTSTRAP_KEY

    mock_compiled[osd.create_osd].side_effect = _create_osd

    try:
        with directory(str(tmpdir)):
            main(
                args=['-v', 'osd', 'storehost1'],
                namespace=ns,
                )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)

    ns.pushy.assert_has_calls([
            mock.call('ssh+sudo:storehost1'),
            mock.call('ssh+sudo:host1'),
        ])
    conn.compile.assert_has_calls([
            mock.call(osd.write_conf),
            mock.call(osd.create_osd),
        ])

    mock_compiled[osd.write_conf].assert_called_once_with(
        cluster='ceph',
        conf="""\
[global]
fsid = 6ede5564-3cf1-44b5-aa96-1c77b0c3e1d0
mon_host = host1

""",
        )

    mock_compiled[osd.create_osd].assert_called_once_with(
        cluster='ceph',
        find_key=mock.ANY,
        )
