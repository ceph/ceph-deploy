from ceph_deploy.lib import remoto
from ceph_deploy.hosts.centos.install import repo_install, mirror_install  # noqa


def install(distro, version_kind, version, adjust_repos):
    logger = distro.conn.logger
    release = distro.release
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    if adjust_repos:
        if version_kind != 'dev':
            remoto.process.run(
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

            remoto.process.run(
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

        if version_kind == 'dev':
            logger.info('skipping install of ceph-release package')
            logger.info('repo file will be created manually')
            mirror_install(
                distro,
                'http://gitbuilder.ceph.com/ceph-rpm-fc{release}-{machine}-basic/ref/{version}/'.format(
                    release=release.split(".", 1)[0],
                    machine=machine,
                    version=version),
                "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc".format(key=key),
                adjust_repos=True,
                extra_installs=False
            )

        # set the right priority
        logger.warning('ensuring that /etc/yum.repos.d/ceph.repo contains a high priority')
        distro.conn.remote_module.set_repo_priority(['Ceph', 'Ceph-noarch', 'ceph-source'])
        logger.warning('altered ceph.repo priorities to contain: priority=1')

    remoto.process.run(
        distro.conn,
        [
            'yum',
            '-y',
            '-q',
            'install',
            'ceph',
        ],
    )
