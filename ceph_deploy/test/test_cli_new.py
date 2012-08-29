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
usage: ceph-deploy new [-h] CLUSTER [MON [MON ...]]

Start deploying a new cluster, and write a CLUSTER.conf for it.

positional arguments:
  CLUSTER     name of the new cluster
  MON         initial monitor hosts

optional arguments:
  -h, --help  show this help message and exit
"""


def test_simple(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'new', 'foo'],
        ):
        pass
    assert {p.basename for p in tmpdir.listdir()} == {'foo.conf'}
    with tmpdir.join('foo.conf').open() as f:
        cfg = conf.parse(f)
    assert cfg.sections() == ['global']


def test_bad_name(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'new', '/evil-this-should-not-be-created'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy new [-h] CLUSTER [MON [MON ...]]
ceph-deploy new: error: argument CLUSTER: argument must start with a letter and contain only letters and numbers
"""

    assert err.value.status == 2
    assert {p.basename for p in tmpdir.listdir()} == set()


def test_exists(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'new', 'foo'],
        ):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'new', 'foo'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
ceph-deploy: Cluster config exists already: foo.conf
"""

    assert err.value.status == 1
    assert {p.basename for p in tmpdir.listdir()} == {'foo.conf'}


def pytest_funcarg__cfg(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    cli = request.getfuncargvalue('cli')
    with cli(
        args=['ceph-deploy', 'new', 'foo'],
        ):
        pass
    with tmpdir.join('foo.conf').open() as f:
        cfg = conf.parse(f)
    return cfg


def test_uuid(cfg):
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
