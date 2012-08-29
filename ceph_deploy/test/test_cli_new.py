import pytest
import subprocess

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
