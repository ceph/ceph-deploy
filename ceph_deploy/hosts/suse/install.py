import logging

from ceph_deploy.util import templates
from ceph_deploy.lib import remoto
from ceph_deploy.hosts.common import map_components

LOG = logging.getLogger(__name__)

NON_SPLIT_PACKAGES = ['ceph-osd', 'ceph-mon', 'ceph-mds']


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.get('components', [])
    )

    distro.packager.clean()
    if packages:
        distro.packager.install(packages)


def mirror_install(distro, repo_url, gpg_url, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.get('components', [])
    )
    repo_url = repo_url.strip('/')  # Remove trailing slashes
    gpg_url_path = gpg_url.split('file://')[-1]  # Remove file if present

    if adjust_repos:
        remoto.process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                gpg_url_path,
            ]
        )

        ceph_repo_content = templates.zypper_repo.format(
            repo_url=repo_url,
            gpg_url=gpg_url
        )
        distro.conn.remote_module.write_file(
            '/etc/zypp/repos.d/ceph.repo',
            ceph_repo_content)
        distro.packager.clean()

    if packages:
        distro.packager.install(packages)


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
    packages = map_components(
        NON_SPLIT_PACKAGES,
        kw.pop('components', [])
    )
    # Get some defaults
    name = kw.get('name', '%s repo' % reponame)
    enabled = kw.get('enabled', 1)
    gpgcheck = kw.get('gpgcheck', 1)
    install_ceph = kw.pop('install_ceph', False)
    proxy = kw.get('proxy')
    _type = 'repo-md'
    baseurl = baseurl.strip('/')  # Remove trailing slashes

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

    distro.conn.remote_module.write_file(
        '/etc/zypp/repos.d/%s' % (reponame),
        repo_content
    )

    # Some custom repos do not need to install ceph
    if install_ceph and packages:
        distro.packager.install(packages)
