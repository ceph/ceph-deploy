import pytest
import subprocess

import ceph_deploy


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
        assert 'usage: ceph-deploy' in result
        assert 'optional arguments:' in result
        assert 'commands:' in result
