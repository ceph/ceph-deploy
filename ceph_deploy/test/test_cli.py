import pytest
import subprocess


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
        assert 'usage: ceph-deploy' in result
        assert 'Deploy Ceph' in result
        assert 'optional arguments:' in result
        assert 'commands:' in result


def test_bad_command(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'bork'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy [-h] [-v] [--cluster NAME] COMMAND ...
ceph-deploy: error: argument COMMAND: invalid choice: 'bork' (choose from 'new', 'install', 'mon', 'osd')
"""

    assert err.value.status == 2
    assert {p.basename for p in tmpdir.listdir()} == set()


def test_bad_cluster(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', '--cluster=/evil-this-should-not-be-created', 'new'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy [-h] [-v] [--cluster NAME] COMMAND ...
ceph-deploy: error: argument --cluster: argument must start with a letter and contain only letters and numbers
"""

    assert err.value.status == 2
    assert {p.basename for p in tmpdir.listdir()} == set()
