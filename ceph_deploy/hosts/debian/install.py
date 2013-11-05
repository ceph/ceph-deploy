from ceph_deploy.lib.remoto import process


def install(distro, version_kind, version, adjust_repos):
    codename = distro.codename
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    # Make sure ca-certificates is installed
    process.run(
        distro.conn,
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

    if adjust_repos:
        process.run(
            distro.conn,
            [
                'wget',
                '-q',
                '-O',
                '{key}.asc'.format(key=key),
                'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc'.format(key=key),
            ],
            stop_on_nonzero=False,
        )

        process.run(
            distro.conn,
            [
                'apt-key',
                'add',
                '{key}.asc'.format(key=key)
            ]
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

        distro.conn.remote_module.write_sources_list(url, codename)

    process.run(
        distro.conn,
        ['apt-get', '-q', 'update'],
        )

    # TODO this does not downgrade -- should it?
    process.run(
        distro.conn,
        [
            'env',
            'DEBIAN_FRONTEND=noninteractive',
            'DEBIAN_PRIORITY=critical',
            'apt-get',
            '-q',
            '-o', 'Dpkg::Options::=--force-confnew',
            '--no-install-recommends',
            '--assume-yes',
            'install',
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
