from ceph_deploy.util.wrappers import check_call
from ceph_deploy.util.context import remote
from ceph_deploy.hosts import common


def install(distro, logger, version_kind, version):
    codename = distro.codename
    machine = distro.sudo_conn.modules.platform.machine()

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    # Make sure ca-certificates is installed
    check_call(
        distro.sudo_conn,
        logger,
        [
            'env',
            'DEBIAN_FRONTEND=noninteractive',
            'apt-get',
            '-q',
            'install',
            '--assume-yes',
            'ca-certificates',
        ]
    )

    check_call(
        distro.sudo_conn,
        logger,
        ['wget -q -O- \'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc\' | apt-key add -'.format(key=key)],
        shell=True,
    )

    if version_kind == 'stable':
        url = 'http://ceph.com/debian-{version}/'.format(
            version=version,
            )
    elif version_kind == 'testing':
        url = 'http://ceph.com/debian-testing/'
    elif version_kind == 'dev':
        url = 'http://gitbuilder.ceph.com/ceph-deb-{codename}-{machine}-basic/ref/{version}'.format(
            codename=codename,
            machine=machine,
            version=version,
            )
    else:
        raise RuntimeError('Unknown version kind: %r' % version_kind)

    def write_sources_list(url, codename):
        """add ceph deb repo to sources.list"""
        with file('/etc/apt/sources.list.d/ceph.list', 'w') as f:
            f.write('deb {url} {codename} main\n'.format(
                    url=url,
                    codename=codename,
                    ))

    with remote(distro.sudo_conn, logger, write_sources_list) as remote_func:
        remote_func(url, codename)

    check_call(
        distro.sudo_conn,
        logger,
        ['apt-get', '-q', 'update'],
        )

    # TODO this does not downgrade -- should it?
    check_call(
        distro.sudo_conn,
        logger,
        [
            'env',
            'DEBIAN_FRONTEND=noninteractive',
            'DEBIAN_PRIORITY=critical',
            'apt-get',
            '-q',
            '-o', 'Dpkg::Options::=--force-confnew',
            'install',
            '--no-install-recommends',
            '--assume-yes',
            '--',
            'ceph',
            'ceph-mds',
            'ceph-common',
            'ceph-fs-common',
            # ceph only recommends gdisk, make sure we actually have
            # it; only really needed for osds, but minimal collateral
            'gdisk',
            ],
        )

    # Check the ceph version
    common.ceph_version(distro.sudo_conn, logger)
