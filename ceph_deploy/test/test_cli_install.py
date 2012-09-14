import argparse
import collections
import mock
import pytest
import subprocess

from ..cli import main
from .. import install

from .directory import directory


def test_help(tmpdir, cli):
    with cli(
        args=['ceph-deploy', 'install', '--help'],
        stdout=subprocess.PIPE,
        ) as p:
        got = p.stdout.read()
        assert got == """\
usage: ceph-deploy install [-h] [--stable [CODENAME] | --testing | --dev
                           [BRANCH_OR_TAG]]
                           HOST [HOST ...]

Install Ceph packages on remote hosts.

positional arguments:
  HOST                  hosts to install on

optional arguments:
  -h, --help            show this help message and exit
  --stable [CODENAME]   install a release known as CODENAME (done by default)
                        (default: argonaut)
  --testing             install the latest development release
  --dev [BRANCH_OR_TAG]
                        install a bleeding edge build from Git branch or tag
                        (default: master)
"""


def test_bad_no_host(tmpdir, cli):
    with pytest.raises(cli.Failed) as err:
        with cli(
            args=['ceph-deploy', 'install'],
            stderr=subprocess.PIPE,
            ) as p:
            got = p.stderr.read()
            assert got == """\
usage: ceph-deploy install [-h] [--stable [CODENAME] | --testing | --dev
                           [BRANCH_OR_TAG]]
                           HOST [HOST ...]
ceph-deploy install: error: too few arguments
"""

    assert err.value.status == 2


def test_simple(tmpdir):
    ns = argparse.Namespace()
    ns.pushy = mock.Mock()
    conn = mock.NonCallableMock(name='PushyClient')
    ns.pushy.return_value = conn

    mock_compiled = collections.defaultdict(mock.Mock)
    conn.compile.side_effect = mock_compiled.__getitem__

    mock_compiled[install.lsb_release].return_value = ('Ubuntu', 'precise')

    try:
        with directory(str(tmpdir)):
            main(
                args=['-v', 'install', 'storehost1'],
                namespace=ns,
                )
    except SystemExit as e:
        raise AssertionError('Unexpected exit: %s', e)

    ns.pushy.assert_has_calls([
            mock.call('ssh+sudo:storehost1'),
        ])

    mock_compiled.pop(install.lsb_release).assert_called_once_with()

    mock_compiled.pop(install.install_ubuntu).assert_called_once_with(
        version_kind='stable',
        codename='precise',
        version='argonaut',
        )

    assert mock_compiled == {}
