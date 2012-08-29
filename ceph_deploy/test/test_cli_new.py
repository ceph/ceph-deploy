import pytest
import re
import subprocess
import uuid

from .. import conf


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'new', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        got = p.stdout.read()
        assert got == """\
usage: ceph-deploy new [-h] [MON [MON ...]]

Start deploying a new cluster, and write a CLUSTER.conf for it.

positional arguments:
  MON         initial monitor hosts

optional arguments:
  -h, --help  show this help message and exit
"""


def test_simple(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'new'],
        ):
        pass
    assert {p.basename for p in tmpdir.listdir()} == {'ceph.conf'}
    with tmpdir.join('ceph.conf').open() as f:
        cfg = conf.parse(f)
    assert cfg.sections() == ['global']


def test_named(tmpdir, cli):
    with cli(
        args=['ceph-deploy', '--cluster=foo', 'new'],
        ):
        pass
    assert {p.basename for p in tmpdir.listdir()} == {'foo.conf'}


def test_exists(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'new'],
        ):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'new'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
ceph-deploy: Cluster config exists already: ceph.conf
"""

    assert err.value.status == 1
    # no temp files left around
    assert {p.basename for p in tmpdir.listdir()} == {'ceph.conf'}


def pytest_funcarg__newcfg(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    cli = request.getfuncargvalue('cli')

    def new(*args):
        with cli(
            args=['ceph-deploy', 'new'] + list(args),
            ):
            pass
        with tmpdir.join('ceph.conf').open() as f:
            cfg = conf.parse(f)
        return cfg
    return new


def test_uuid(newcfg):
    cfg = newcfg()
    fsid = cfg.get('global', 'fsid')
    # make sure it's a valid uuid
    uuid.UUID(hex=fsid)
    # make sure it looks pretty, too
    UUID_RE = re.compile(
        r'^[0-9a-f]{8}-'
        + r'[0-9a-f]{4}-'
        # constant 4 here, we want to enforce randomness and not leak
        # MACs or time
        + r'4[0-9a-f]{3}-'
        + r'[0-9a-f]{4}-'
        + r'[0-9a-f]{12}$',
        )
    assert UUID_RE.match(fsid)


def test_mons(newcfg):
    cfg = newcfg('node01', 'node07', 'node34')
    mon_initial_members = cfg.get('global', 'mon_initial_members')
    assert mon_initial_members == 'node01, node07, node34'
