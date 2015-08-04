from ceph_deploy.util import templates


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = kw.get('components', [])
    distro.packager.clean()
    distro.packager.install(packages)


def mirror_install(distro, repo_url,
                   gpg_url, adjust_repos, extra_installs=True, **kw):
    packages = kw.get('components', [])
    repo_url = repo_url.strip('/')  # Remove trailing slashes

    distro.packager.clean()

    if adjust_repos:
        distro.packager.add_repo_gpg_key(gpg_url)

        ceph_repo_content = templates.ceph_repo.format(
            repo_url=repo_url,
            gpg_url=gpg_url
        )

        distro.conn.remote_module.write_yum_repo(ceph_repo_content)

    if extra_installs and packages:
        distro.packager.install(packages)


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
    # do we have specific components to install?
    # removed them from `kw` so that we don't mess with other defaults
    packages = kw.pop('components', [])

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

    # Some custom repos do not need to install ceph
    if install_ceph and packages:
        distro.packager.install(packages)
