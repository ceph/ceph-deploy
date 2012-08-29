import pytest
import subprocess


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        got = p.stdout.read()
        assert got == """\
usage: ceph-deploy [-h] [-v] COMMAND ...

Deploy Ceph

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  be more verbose

commands:
  COMMAND        description
    new          Start deploying a new cluster, and write a CLUSTER.conf for
                 it.
"""


def test_bad_command(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'bork'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy [-h] [-v] COMMAND ...
ceph-deploy: error: argument COMMAND: invalid choice: 'bork' (choose from 'new')
"""

    assert err.value.status == 2
    assert {p.basename for p in tmpdir.listdir()} == set()
