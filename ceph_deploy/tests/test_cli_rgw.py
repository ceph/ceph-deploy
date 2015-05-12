import pytest
import subprocess

import ceph_deploy.rgw as rgw


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'rgw', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
    assert 'usage: ceph-deploy rgw' in result
    assert 'positional arguments' in result
    assert 'optional arguments' in result


def test_bad_no_conf(tmpdir, cli):
    with tmpdir.join('ceph.conf').open('w'):
        pass
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'rgw'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read()
    assert 'usage: ceph-deploy rgw' in result
    assert err.value.status == 2


def test_rgw_prefix_auto():
    daemon = rgw.colon_separated("hostname")
    assert daemon == ("hostname", "rgw.hostname")


def test_rgw_prefix_custom():
    daemon = rgw.colon_separated("hostname:mydaemon")
    assert daemon == ("hostname", "rgw.mydaemon")
