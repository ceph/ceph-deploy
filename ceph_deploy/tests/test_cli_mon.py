import argparse
import collections
import mock
import pytest
import subprocess

from ..cli import main
from .. import mon

from .directory import directory
from .fakes import fake_getaddrinfo

def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'mon', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
    assert 'usage: ceph-deploy' in result
    assert 'positional arguments:' in result
    assert 'optional arguments:' in result


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
            result = p.stderr.read()
    assert 'usage: ceph-deploy mon' in result
    assert 'too few arguments' in result
    assert err.value.status == 2


def test_simple(tmpdir, capsys):
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

    try:
        with mock.patch('ceph_deploy.new.socket.gethostbyname'):
            with mock.patch('socket.getaddrinfo', fake_getaddrinfo):
                with directory(str(tmpdir)):
                    main(
                        args=['-v', 'new', 'host1'],
                        namespace=ns,
                        )
                    main(
                        args=['-v', 'mon', 'create', 'host1'],
                        namespace=ns,
                        )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)
    out, err = capsys.readouterr()
    err = err.lower()
    assert 'creating new cluster named ceph' in err
    assert 'monitor host1 at h' in err
    assert 'resolving host host1' in err
    assert "monitor initial members are ['host1']" in err
    assert "monitor addrs are ['h']" in err
