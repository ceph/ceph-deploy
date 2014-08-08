from ceph_deploy.util import pkg_managers, templates
from ceph_deploy.lib import remoto


def rpm_dist(distro):
    if distro.normalized_name in ['redhat', 'centos', 'scientific'] and distro.normalized_release.int_major >= 6:
        return 'el' + distro.normalized_release.major
    return 'el6'


def repository_url_part(distro):
    """
    Historically everything CentOS, RHEL, and Scientific has been mapped to
    `el6` urls, but as we are adding repositories for `rhel`, the URLs should
    map correctly to, say, `rhel6` or `rhel7`.

    This function looks into the `distro` object and determines the right url
    part for the given distro, falling back to `el6` when all else fails.

    Specifically to work around the issue of CentOS vs RHEL::

        >>> import platform
        >>> platform.linux_distribution()
        ('Red Hat Enterprise Linux Server', '7.0', 'Maipo')

    """
    if distro.normalized_release.int_major >= 6:
        if distro.normalized_name == 'redhat':
            return 'rhel' + distro.normalized_release.major
        if distro.normalized_name in ['centos', 'scientific']:
            return 'el' + distro.normalized_release.major

    return 'el6'


def install(distro, version_kind, version, adjust_repos):
    logger = distro.conn.logger
    release = distro.release
    machine = distro.machine_type
    repo_part = repository_url_part(distro)
    dist = rpm_dist(distro)

    pkg_managers.yum_clean(distro.conn)

    # Even before EPEL, make sure we have `wget`
    pkg_managers.yum(distro.conn, 'wget')

    # Get EPEL installed before we continue:
    if adjust_repos:
        install_epel(distro)
        install_yum_priorities(distro)
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
                url = 'http://ceph.com/rpm-{version}/{repo}/'.format(
                    version=version,
                    repo=repo_part,
                    )
            elif version_kind == 'testing':
                url = 'http://ceph.com/rpm-testing/{repo}/'.format(repo=repo_part)

            remoto.process.run(
                distro.conn,
                [
                    'rpm',
                    '-Uvh',
                    '--replacepkgs',
                    '{url}noarch/ceph-release-1-0.{dist}.noarch.rpm'.format(url=url, dist=dist),
                ],
            )

        if version_kind == 'dev':
            logger.info('skipping install of ceph-release package')
            logger.info('repo file will be created manually')
            mirror_install(
                distro,
                'http://gitbuilder.ceph.com/ceph-rpm-centos{release}-{machine}-basic/ref/{version}/'.format(
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
            'install',
            'ceph',
        ],
    )


def install_epel(distro):
    """
    CentOS and Scientific need the EPEL repo, otherwise Ceph cannot be
    installed.
    """
    if distro.name.lower() in ['centos', 'scientific']:
        distro.conn.logger.info('adding EPEL repository')
        if float(distro.release) >= 6:
            remoto.process.run(
                distro.conn,
                ['wget', 'http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm'],
            )
            pkg_managers.rpm(
                distro.conn,
                [
                    '--replacepkgs',
                    'epel-release-6*.rpm',
                ],
            )
        else:
            remoto.process.run(
                distro.conn,
                ['wget', 'http://dl.fedoraproject.org/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm'],
            )
            pkg_managers.rpm(
                distro.conn,
                [
                    '--replacepkgs',
                    'epel-release-5*.rpm'
                ],
            )


def install_yum_priorities(distro):
    """
    EPEL started packaging Ceph so we need to make sure that the ceph.repo we
    install has a higher priority than the EPEL repo so that when installing
    Ceph it will come from the repo file we create.

    The name of the package changed back and forth (!) since CentOS 4:

    From the CentOS wiki::

        Note: This plugin has carried at least two differing names over time.
        It is named yum-priorities on CentOS-5 but was named
        yum-plugin-priorities on CentOS-4. CentOS-6 has reverted to
        yum-plugin-priorities.

    """
    if distro.normalized_name == 'centos':
        if distro.release[0] == '6':
            package_name = 'yum-plugin-priorities'
        else:
            package_name = 'yum-priorities'

        pkg_managers.yum(
            distro.conn,
            package_name,
        )


def mirror_install(distro, repo_url, gpg_url, adjust_repos, extra_installs=True):
    repo_url = repo_url.strip('/')  # Remove trailing slashes
    gpg_url_path = gpg_url.split('file://')[-1]  # Remove file if present

    pkg_managers.yum_clean(distro.conn)

    if adjust_repos:
        remoto.process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                gpg_url_path,
            ]
        )

        ceph_repo_content = templates.ceph_repo.format(
            repo_url=repo_url,
            gpg_url=gpg_url
        )

        distro.conn.remote_module.write_yum_repo(ceph_repo_content)

    if extra_installs:
        # Before any install, make sure we have `wget`
        pkg_managers.yum(distro.conn, 'wget')

        pkg_managers.yum(distro.conn, 'ceph')


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
    # Get some defaults
    name = kw.get('name', '%s repo' % reponame)
    enabled = kw.get('enabled', 1)
    gpgcheck = kw.get('gpgcheck', 1)
    install_ceph = kw.pop('install_ceph', False)
    proxy = kw.get('proxy')
    _type = 'repo-md'
    baseurl = baseurl.strip('/')  # Remove trailing slashes

    pkg_managers.yum_clean(distro.conn)

    if gpgkey:
        remoto.process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                gpgkey,
            ]
        )

    repo_content = templates.custom_repo(
        reponame=reponame,
        name = name,
        baseurl = baseurl,
        enabled = enabled,
        gpgcheck = gpgcheck,
        _type = _type,
        gpgkey = gpgkey,
        proxy = proxy,
    )

    distro.conn.remote_module.write_yum_repo(
        repo_content,
        "%s.repo" % reponame
    )

    # Some custom repos do not need to install ceph
    if install_ceph:
        # Before any install, make sure we have `wget`
        pkg_managers.yum(distro.conn, 'wget')

        pkg_managers.yum(distro.conn, 'ceph')
