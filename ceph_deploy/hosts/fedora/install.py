from ceph_deploy.lib.remoto import process


def install(distro, version_kind, version, adjust_repos):
    release = distro.release
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    if adjust_repos:
        process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc".format(key=key)
            ]
        )

        if version_kind == 'stable':
            url = 'http://ceph.com/rpm-{version}/fc{release}/'.format(
                version=version,
                release=release,
                )
        elif version_kind == 'testing':
            url = 'http://ceph.com/rpm-testing/fc{release}'.format(
                release=release,
                )
        elif version_kind == 'dev':
            url = 'http://gitbuilder.ceph.com/ceph-rpm-fc{release}-{machine}-basic/ref/{version}/'.format(
                release=release.split(".", 1)[0],
                machine=machine,
                version=version,
                )

        process.run(
            distro.conn,
            [
                'rpm',
                '-Uvh',
                '--replacepkgs',
                '--force',
                '--quiet',
                '{url}noarch/ceph-release-1-0.fc{release}.noarch.rpm'.format(
                    url=url,
                    release=release,
                    ),
            ]
        )

    process.run(
        distro.conn,
        [
            'yum',
            '-y',
            '-q',
            'install',
            'ceph',
        ],
    )
