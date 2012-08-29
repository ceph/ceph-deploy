import pytest
import subprocess


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'mon', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        got = p.stdout.read()
        assert got == """\
usage: ceph-deploy mon [-h] [MON [MON ...]]

Deploy ceph monitor on remote hosts.

positional arguments:
  MON         host to deploy on

optional arguments:
  -h, --help  show this help message and exit
"""


def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'mon'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
ceph-deploy: Cannot load config: [Errno 2] No such file or directory: 'ceph.conf'
"""

    assert err.value.status == 1


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
