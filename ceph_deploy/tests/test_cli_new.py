import re
import uuid

from mock import patch

from ceph_deploy import conf
from ceph_deploy.cli import _main as main
from ceph_deploy.tests.directory import directory


def test_write_global_conf_section(tmpdir):
    fake_ip_addresses = lambda x: ['10.0.0.1']

    with patch('ceph_deploy.new.hosts'):
        with patch('ceph_deploy.new.net.ip_addresses', fake_ip_addresses):
            with patch('ceph_deploy.new.net.get_nonlocal_ip', lambda x: '10.0.0.1'):
                with patch('ceph_deploy.new.arg_validators.Hostname', lambda: lambda x: x):
                    with directory(str(tmpdir)):
                        main(args=['new', 'host1'])
    with tmpdir.join('ceph.conf').open() as f:
        cfg = conf.ceph.parse(f)
    assert cfg.sections() == ['global']


def pytest_funcarg__newcfg(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    fake_ip_addresses = lambda x: ['10.0.0.1']

    def new(*args):
        with patch('ceph_deploy.new.net.ip_addresses', fake_ip_addresses):
            with patch('ceph_deploy.new.hosts'):
                with patch('ceph_deploy.new.net.get_nonlocal_ip', lambda x: '10.0.0.1'):
                    with patch('ceph_deploy.new.arg_validators.Hostname', lambda: lambda x: x):
                        with directory(str(tmpdir)):
                            main(args=['new'] + list(args))
                            with tmpdir.join('ceph.conf').open() as f:
                                cfg = conf.ceph.parse(f)
                            return cfg
    return new


def test_uuid(newcfg):
    cfg = newcfg('host1')
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


def test_defaults(newcfg):
    cfg = newcfg('host1')
    assert cfg.get('global', 'auth cluster required') == 'cephx'
    assert cfg.get('global', 'auth service required') == 'cephx'
    assert cfg.get('global', 'auth client required') == 'cephx'
