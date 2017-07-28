import logging
from ceph_deploy.util import templates
from ceph_deploy.lib import remoto
from ceph_deploy.hosts.common import map_components
from ceph_deploy.util.paths import gpg
from ceph_deploy.util import net


LOG = logging.getLogger(__name__)
NON_SPLIT_PACKAGES = ['ceph-osd', 'ceph-mon', 'ceph-mds']


def rpm_dist(distro):
    if distro.normalized_name in ['redhat', 'centos', 'scientific', 'oracle', 'virtuozzo'] and distro.normalized_release.int_major >= 6:
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
        if distro.normalized_name in ['centos', 'scientific', 'oracle', 'virtuozzo']:
            return 'el' + distro.normalized_release.major

    return 'el6'


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.pop('components', [])
    )

    gpgcheck = kw.pop('gpgcheck', 1)
    logger = distro.conn.logger
    machine = distro.machine_type
    repo_part = repository_url_part(distro)
    dist = rpm_dist(distro)

    distro.packager.clean()

    # Get EPEL installed before we continue:
    if adjust_repos:
        distro.packager.install('epel-release')
        distro.packager.install('yum-plugin-priorities')
        distro.conn.remote_module.enable_yum_priority_obsoletes()
        logger.warning('check_obsoletes has been enabled for Yum priorities plugin')
    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    if adjust_repos:
        if version_kind in ['stable', 'testing']:
            distro.packager.add_repo_gpg_key(gpg.url(key))

            if version_kind == 'stable':
                url = 'https://download.ceph.com/rpm-{version}/{repo}/'.format(
                    version=version,
                    repo=repo_part,
                    )
            elif version_kind == 'testing':
                url = 'https://download.ceph.com/rpm-testing/{repo}/'.format(repo=repo_part)

            # remove any old ceph-release package from prevoius release
            remoto.process.run(
                distro.conn,
                [
                    'yum',
                    'remove',
                    '-y',
                    'ceph-release'
                ],
            )
            remoto.process.run(
                distro.conn,
                [
                    'yum',
                    'install',
                    '-y',
                    '{url}noarch/ceph-release-1-0.{dist}.noarch.rpm'.format(url=url, dist=dist),
                ],
            )

        elif version_kind in ['dev', 'dev_commit']:
            logger.info('skipping install of ceph-release package')
            logger.info('repo file will be created manually')
            shaman_url = 'https://shaman.ceph.com/api/repos/ceph/{version}/{sha1}/{distro}/{distro_version}/repo/?arch={arch}'.format(
                distro=distro.normalized_name,
                distro_version=distro.normalized_release.major,
                version=kw['args'].dev,
                sha1=kw['args'].dev_commit or 'latest',
                arch=machine
                )
            LOG.debug('fetching repo information from: %s' % shaman_url)
            content = net.get_chacra_repo(shaman_url)
            mirror_install(
                distro,
                '',  # empty repo_url
                None,  # no need to use gpg here, repos are unsigned
                adjust_repos=True,
                extra_installs=False,
                gpgcheck=gpgcheck,
                repo_content=content
            )

        else:
            raise Exception('unrecognized version_kind %s' % version_kind)

        # set the right priority
        logger.warning('ensuring that /etc/yum.repos.d/ceph.repo contains a high priority')
        distro.conn.remote_module.set_repo_priority(['Ceph', 'Ceph-noarch', 'ceph-source'])
        logger.warning('altered ceph.repo priorities to contain: priority=1')

    if packages:
        distro.packager.install(packages)


def mirror_install(distro, repo_url, gpg_url, adjust_repos, extra_installs=True, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.pop('components', [])
    )
    repo_url = repo_url.strip('/')  # Remove trailing slashes
    gpgcheck = kw.pop('gpgcheck', 1)

    distro.packager.clean()

    if adjust_repos:
        if gpg_url:
            distro.packager.add_repo_gpg_key(gpg_url)

        ceph_repo_content = templates.ceph_repo.format(
            repo_url=repo_url,
            gpg_url=gpg_url,
            gpgcheck=gpgcheck,
        )
        content = kw.get('repo_content', ceph_repo_content)

        distro.conn.remote_module.write_yum_repo(content)
        # set the right priority
        if distro.packager.name == 'yum':
            distro.packager.install('yum-plugin-priorities')
        distro.conn.remote_module.set_repo_priority(['Ceph', 'Ceph-noarch', 'ceph-source'])
        distro.conn.logger.warning('altered ceph.repo priorities to contain: priority=1')


    if extra_installs and packages:
        distro.packager.install(packages)


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.pop('components', [])
    )
    logger = distro.conn.logger
    # Get some defaults
    name = kw.pop('name', '%s repo' % reponame)
    enabled = kw.pop('enabled', 1)
    gpgcheck = kw.pop('gpgcheck', 1)
    install_ceph = kw.pop('install_ceph', False)
    proxy = kw.pop('proxy', '') # will get ignored if empty
    _type = 'repo-md'
    baseurl = baseurl.strip('/')  # Remove trailing slashes

    distro.packager.clean()

    if gpgkey:
        distro.packager.add_repo_gpg_key(gpgkey)

    repo_content = templates.custom_repo(
        reponame=reponame,
        name=name,
        baseurl=baseurl,
        enabled=enabled,
        gpgcheck=gpgcheck,
        _type=_type,
        gpgkey=gpgkey,
        proxy=proxy,
        **kw
    )

    distro.conn.remote_module.write_yum_repo(
        repo_content,
        "%s.repo" % reponame
    )

    repo_path = '/etc/yum.repos.d/{reponame}.repo'.format(reponame=reponame)

    # set the right priority
    if kw.get('priority'):
        if distro.packager.name == 'yum':
            distro.packager.install('yum-plugin-priorities')

        distro.conn.remote_module.set_repo_priority([reponame], repo_path)
        logger.warning('altered {reponame}.repo priorities to contain: priority=1'.format(
            reponame=reponame)
        )

    # Some custom repos do not need to install ceph
    if install_ceph and packages:
        distro.packager.install(packages)
