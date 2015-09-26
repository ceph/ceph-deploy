from ceph_deploy.lib import remoto
from ceph_deploy.hosts.centos.install import repo_install, mirror_install  # noqa
from ceph_deploy.util.paths import gpg
from ceph_deploy.hosts.common import map_components


NON_SPLIT_PACKAGES = ['ceph-osd', 'ceph-mon', 'ceph-mds']


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.pop('components', [])
    )
    logger = distro.conn.logger
    release = distro.release
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    if adjust_repos:
        if distro.packager.name == 'yum':
            distro.packager.install('yum-plugin-priorities')
            # haven't been able to determine necessity of check_obsoletes with DNF
            distro.conn.remote_module.enable_yum_priority_obsoletes()
            logger.warning('check_obsoletes has been enabled for Yum priorities plugin')

        if version_kind in ['stable', 'testing']:
            distro.packager.add_repo_gpg_key(gpg.url(key))

            if version_kind == 'stable':
                url = 'http://download.ceph.com/rpm-{version}/fc{release}/'.format(
                    version=version,
                    release=release,
                    )
            elif version_kind == 'testing':
                url = 'http://download.ceph.com/rpm-testing/fc{release}'.format(
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

            # set the right priority
            logger.warning('ensuring that /etc/yum.repos.d/ceph.repo contains a high priority')
            distro.conn.remote_module.set_repo_priority(['Ceph', 'Ceph-noarch', 'ceph-source'])
            logger.warning('altered ceph.repo priorities to contain: priority=1')

        elif version_kind in ['dev', 'dev_commit']:
            logger.info('skipping install of ceph-release package')
            logger.info('repo file will be created manually')
            mirror_install(
                distro,
                'http://{gitbuilder_host}/ceph-rpm-fc{release}-{machine}-basic/{sub}/{version}/'.format(
                    release=release.split(".", 1)[0],
                    machine=machine,
                    sub='ref' if version_kind == 'dev' else 'sha1',
                    version=version),
                gpg.url(key),
                adjust_repos=True,
                extra_installs=False,
                gitbuilder_host=kw['gitbuilder_host'],
            )

        else:
            raise Exception('unrecognized version_kind %s' % version_kind)

    distro.packager.install(
        packages
    )
