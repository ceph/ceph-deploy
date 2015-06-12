from ceph_deploy.util import templates, pkg_managers
from ceph_deploy.lib import remoto
import logging

LOG = logging.getLogger(__name__)


def map_components(components):
    # SUSE distributions don't offer the same granularity of packages as
    # used by ceph-deploy, so we need to do some mapping.
    packages = []

    if (('ceph-osd' in components)
     or ('ceph-mds' in components)
     or ('ceph-mon' in components)):
        packages.append('ceph')
    if 'ceph-common' in components:
        packages.append('ceph-common')
    if 'ceph-radosgw' in components:
        packages.append('ceph-radosgw')

    return packages


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = map_components(kw.get('components', []))

    pkg_managers.zypper_refresh(distro.conn)
    if len(packages):
        pkg_managers.zypper(distro.conn, packages)


def mirror_install(distro, repo_url, gpg_url, adjust_repos, **kw):
    packages = map_components(kw.get('components', []))
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
        pkg_managers.zypper_refresh(distro.conn)

    if len(packages):
        pkg_managers.zypper(distro.conn, packages)


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
    # do we have specific components to install?
    # removed them from `kw` so that we don't mess with other defaults
    packages = map_components(kw.pop('components', []))  # noqa
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
    if install_ceph and len(packages):
        pkg_managers.zypper(distro.conn, packages)
