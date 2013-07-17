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
        result = p.stdout.read()
    assert 'usage: ceph-deploy osd' in result
    assert 'positional arguments' in result
    assert 'optional arguments' in result


def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'osd', 'fakehost:/does-not-exist'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
    assert 'ceph-deploy osd: error' in result
    assert 'invalid choice' in result
    assert err.value.status == 2


def test_bad_no_disk(tmpdir, cli):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'osd'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
    assert 'usage: ceph-deploy osd' in result
    assert err.value.status == 2


def test_simple(tmpdir, capsys):
    with tmpdir.join('ceph.conf').open('w') as f:
        f.write("""\
[global]
fsid = 6ede5564-3cf1-44b5-aa96-1c77b0c3e1d0
mon host = host1
""")

    ns = argparse.Namespace()

    conn_osd = mock.NonCallableMock(name='PushyClient-osd')
    mock_compiled_osd = collections.defaultdict(mock.Mock)
    #conn_osd.compile.side_effect = mock_compiled_osd.__getitem__
    conn_osd.compile.return_value = mock.Mock(return_value='fakekeyring')

    conn_mon = mock.NonCallableMock(name='PushyClient-mon')
    mock_compiled_mon = collections.defaultdict(mock.Mock)
    conn_mon.compile.side_effect = mock_compiled_mon.__getitem__

    ns.pushy = mock.Mock(name='pushy namespace')

    def _conn(url):
        if url == 'ssh+sudo:host1':
            return conn_mon
        elif url == 'ssh+sudo:storehost1:sdc':
            return conn_osd
        else:
            raise AssertionError('Unexpected connection url: %r', url)
    ns.pushy.side_effect = _conn

    BOOTSTRAP_KEY = 'fakekeyring'

    mock_compiled_mon[osd.get_bootstrap_osd_key].side_effect = BOOTSTRAP_KEY

    def _create_osd(cluster, find_key):
        key = find_key()
        assert key == BOOTSTRAP_KEY

    mock_compiled_osd[osd.create_osd].side_effect = _create_osd

    with directory(str(tmpdir)):
        main(
            args=['-v', 'gatherkeys', 'storehost1:sdc'],
            namespace=ns,
        )
        main(
            args=['-v', 'osd', 'prepare', 'storehost1:sdc'],
            namespace=ns,
            )
    out, err = capsys.readouterr()
    err = err.lower()
    assert 'have ceph.mon.keyring' in err
    assert 'have ceph.client.admin.keyring' in err
    assert 'have ceph.bootstrap-osd.keyring' in err
    assert 'got ceph.bootstrap-mds.keyring key from storehost1:sdc' in err
    assert 'got ceph.bootstrap-osd.keyring key from storehost1:sdc' in err
