import subprocess

import pytest
from mock import Mock, patch

from ceph_deploy.cli import _main as main
from ceph_deploy.tests.directory import directory
from ceph_deploy.tests.util import assert_too_few_arguments


#TODO: This test does check that things fail if the .conf file is missing
def test_bad_no_conf(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'mon'],
            stderr=subprocess.PIPE,
            ) as p:
            result = p.stderr.read().decode('utf-8')
    assert 'usage: ceph-deploy' in result
    assert_too_few_arguments(result)
    assert err.value.status == 2


def make_fake_connection(platform_information=None):
    get_connection = Mock()
    get_connection.return_value = get_connection
    get_connection.remote_module.platform_information = Mock(
        return_value=platform_information)
    return get_connection


def test_new(tmpdir, capsys):
    with tmpdir.join('ceph.conf').open('w') as f:
        f.write("""\
[global]
fsid = 6ede5564-3cf1-44b5-aa96-1c77b0c3e1d0
mon initial members = host1
""")

    fake_ip_addresses = lambda x: ['10.0.0.1']
    try:
        with patch('ceph_deploy.new.net.ip_addresses', fake_ip_addresses):
            with patch('ceph_deploy.new.net.get_nonlocal_ip', lambda x: '10.0.0.1'):
                with patch('ceph_deploy.new.arg_validators.Hostname', lambda: lambda x: x):
                    with patch('ceph_deploy.new.hosts'):
                        with directory(str(tmpdir)):
                            main(['-v', 'new', '--no-ssh-copykey', 'host1'])
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)
    out, err = capsys.readouterr()
    err = err.lower()
    assert 'creating new cluster named ceph' in err
    assert 'monitor host1 at 10.0.0.1' in err
    assert 'resolving host host1' in err
    assert "monitor initial members are ['host1']" in err
    assert "monitor addrs are ['10.0.0.1']" in err
