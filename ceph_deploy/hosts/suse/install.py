from ceph_deploy.lib.remoto import process


def install(distro, version_kind, version, adjust_repos):
    release = distro.release
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    if distro.codename == 'Mantis':
        distro = 'opensuse12'
    else:
        distro = 'sles-11sp2'

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
            url = 'http://ceph.com/rpm-{version}/{distro}/'.format(
                version=version,
                distro=distro,
                )
        elif version_kind == 'testing':
            url = 'http://ceph.com/rpm-testing/{distro}'.format(distro=distro)
        elif version_kind == 'dev':
            url = 'http://gitbuilder.ceph.com/ceph-rpm-{distro}{release}-{machine}-basic/ref/{version}/'.format(
                distro=distro,
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
                '{url}noarch/ceph-release-1-0.noarch.rpm'.format(
                    url=url,
                    ),
                ]
            )

    process.run(
        distro.conn,
        [
            'zypper',
            '--non-interactive',
            '--quiet',
            'install',
            'ceph',
            ],
        )
