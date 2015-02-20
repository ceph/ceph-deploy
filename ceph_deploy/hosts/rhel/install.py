from ceph_deploy.util import pkg_managers, templates
from ceph_deploy.lib import remoto


def install(distro, version_kind, version, adjust_repos):
    pkg_managers.yum_clean(distro.conn)
    pkg_managers.yum(distro.conn, ['ceph', 'ceph-mon', 'ceph-osd'])


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
        pkg_managers.yum(distro.conn, ['ceph', 'ceph-mon', 'ceph-osd'])


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
    # Get some defaults
    name = kw.pop('name', '%s repo' % reponame)
    enabled = kw.pop('enabled', 1)
    gpgcheck = kw.pop('gpgcheck', 1)
    install_ceph = kw.pop('install_ceph', False)
    proxy = kw.pop('proxy', '') # will get ignored if empty
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
    if install_ceph:
        pkg_managers.yum(distro.conn, ['ceph', 'ceph-mon', 'ceph-osd'])
