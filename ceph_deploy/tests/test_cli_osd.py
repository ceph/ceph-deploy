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
