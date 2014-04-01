from ceph_deploy.util import templates, pkg_managers
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
            url = 'http://ceph.com/rpm-testing/{distro}/'.format(distro=distro)
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


def mirror_install(distro, repo_url, gpg_url, adjust_repos):
    repo_url = repo_url.strip('/')  # Remove trailing slashes

    if adjust_repos:
        process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                gpg_url,
            ]
        )

        ceph_repo_content = templates.ceph_repo.format(
            repo_url=repo_url,
            gpg_url=gpg_url
        )

        distro.conn.remote_module.write_yum_repo(ceph_repo_content)

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


def repo_install(distro, repo_name, baseurl, gpgkey, **kw):
    # Get some defaults
    name = kw.get('name', '%s repo' % repo_name)
    enabled = kw.get('enabled', 1)
    gpgcheck = kw.get('gpgcheck', 1)
    install_ceph = kw.pop('install_ceph', False)
    _type = 'repo-md'
    baseurl = baseurl.strip('/')  # Remove trailing slashes

    if gpgkey:
        process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                gpgkey,
            ]
        )

    repo_content = templates.custom_repo.format(
        repo_name=repo_name,
        name = name,
        baseurl = baseurl,
        enabled = enabled,
        gpgcheck = gpgcheck,
        _type = _type,
        gpgkey = gpgkey,
    )

    distro.conn.remote_module.write_yum_repo(
        repo_content,
        "%s.repo" % repo_name
    )

    # Some custom repos do not need to install ceph
    if install_ceph:
        # Before any install, make sure we have `wget`
        pkg_managers.zypper(distro.conn, 'wget')

        pkg_managers.zypper(distro.conn, 'ceph')
