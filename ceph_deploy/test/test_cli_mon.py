import argparse
import collections
import mock
import pytest
import subprocess

from ..cli import main
from .. import mon

from .directory import directory


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'mon', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
    assert 'usage: ceph-deploy' in result
    assert 'Deploy ceph monitor on remote hosts.' in result
    assert 'positional arguments:'
    assert 'optional arguments:'


def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'mon'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
    assert 'usage: ceph-deploy' in result
    assert 'too few arguments' in result
    assert err.value.status == 2


def test_bad_no_mon(tmpdir, cli):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'mon'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
ceph-deploy: No hosts specified to deploy to.
"""

    assert err.value.status == 1


def test_simple(tmpdir):
    with tmpdir.join('ceph.conf').open('w') as f:
        f.write("""\
[global]
fsid = 6ede5564-3cf1-44b5-aa96-1c77b0c3e1d0
mon initial members = host1
""")

    ns = argparse.Namespace()
    ns.pushy = mock.Mock()
    conn = mock.NonCallableMock(name='PushyClient')
    ns.pushy.return_value = conn

    mock_compiled = collections.defaultdict(mock.Mock)
    conn.compile.side_effect = mock_compiled.__getitem__

    MON_SECRET = 'AQBWDj5QAP6LHhAAskVBnUkYHJ7eYREmKo5qKA=='

    def _create_mon(cluster, get_monitor_secret):
        secret = get_monitor_secret()
        assert secret == MON_SECRET

    mock_compiled[mon.create_mon].side_effect = _create_mon

    try:
        with directory(str(tmpdir)):
            main(
                args=['-v', 'mon'],
                namespace=ns,
                )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)

    ns.pushy.assert_called_once_with('ssh+sudo:host1')

    mock_compiled.pop(mon.write_conf).assert_called_once_with(
        cluster='ceph',
        conf="""\
[global]
fsid = 6ede5564-3cf1-44b5-aa96-1c77b0c3e1d0
mon_initial_members = host1

""",
        )

    mock_compiled.pop(mon.create_mon).assert_called_once_with(
        cluster='ceph',
        get_monitor_secret=mock.ANY,
        )

    assert mock_compiled == {}
