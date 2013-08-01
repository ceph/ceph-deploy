import pytest
from mock import patch
import re
import subprocess
import uuid

from .. import conf
from ..cli import main
from .directory import directory
from .fakes import fake_getaddrinfo


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'new', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        result = p.stdout.read()
    assert 'usage: ceph-deploy new' in result
    assert 'positional arguments' in result
    assert 'optional arguments' in result


def test_write_global_conf_section(tmpdir, cli):
    with patch('ceph_deploy.new.socket.gethostbyname'):
        with patch('ceph_deploy.new.socket.getaddrinfo', fake_getaddrinfo):
            with directory(str(tmpdir)):
                main(args=['new', 'host1'])
    with tmpdir.join('ceph.conf').open() as f:
        cfg = conf.parse(f)
    assert cfg.sections() == ['global']


def pytest_funcarg__newcfg(request):
    tmpdir = request.getfuncargvalue('tmpdir')
    cli = request.getfuncargvalue('cli')

    def new(*args):
        with patch('ceph_deploy.new.socket.gethostbyname'):
            with patch('ceph_deploy.new.socket.getaddrinfo', fake_getaddrinfo):
                with directory(str(tmpdir)):
                    main( args=['new'] + list(args))
                    with tmpdir.join('ceph.conf').open() as f:
                        cfg = conf.parse(f)
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
    assert cfg.get('global', 'auth_supported') == 'cephx'
    assert cfg.get('global', 'osd_journal_size') == '1024'
    assert cfg.get('global', 'filestore_xattr_use_omap') == 'true'
