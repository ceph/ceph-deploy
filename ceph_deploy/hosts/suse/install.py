from ceph_deploy.util.wrappers import check_call
from ceph_deploy.hosts import common


def install(distro, logger, version_kind, version, adjust_repos):
    release = distro.release
    machine = distro.sudo_conn.modules.platform.machine()

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    if distro.codename == 'Mantis':
        distro = 'opensuse12'
    else:
        distro = 'sles-11sp2'

    if adjust_repos:
        check_call(
            distro.sudo_conn,
            logger,
            ['su -c \'rpm --import "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc"\''.format(key=key)],
            shell=True,
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

        check_call(
            distro.sudo_conn,
            logger,
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

    check_call(
        distro.sudo_conn,
        logger,
        [
            'zypper',
            '--non-interactive',
            '--quiet',
            'install',
            'ceph',
            ],
        )

    # Check the ceph version
    common.ceph_version(distro.sudo_conn, logger)
