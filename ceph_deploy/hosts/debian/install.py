

def install(release, codename, version_kind, version):
    import platform
    import subprocess

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    subprocess.check_call(
        args='wget -q -O- \'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc\' | apt-key add -'.format(key=key),
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
            machine=platform.machine(),
            version=version,
            )
    else:
        raise RuntimeError('Unknown version kind: %r' % version_kind)

    with file('/etc/apt/sources.list.d/ceph.list', 'w') as f:
        f.write('deb {url} {codename} main\n'.format(
                url=url,
                codename=codename,
                ))

    subprocess.check_call(
        args=[
            'apt-get',
            '-q',
            'update',
            ],
        )

    # TODO this does not downgrade -- should it?
    subprocess.check_call(
        args=[
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
