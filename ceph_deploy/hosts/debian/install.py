from urlparse import urlparse

from ceph_deploy.util.paths import gpg
from ceph_deploy.hosts.common import map_components


NON_SPLIT_COMPONENTS = ['ceph-osd', 'ceph-mon']


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_COMPONENTS,
        kw.pop('components', [])
    )
    codename = distro.codename
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    distro.packager.install(['ca-certificates', 'apt-transport-https'])

    if adjust_repos:
        # Wheezy does not like the download.ceph.com SSL cert
        protocol = 'https'
        if codename == 'wheezy':
            protocol = 'http'
        distro.packager.add_repo_gpg_key(gpg.url(key, protocol=protocol))

        if version_kind == 'stable':
            url = '{protocol}://download.ceph.com/debian-{version}/'.format(
                protocol=protocol,
                version=version,
                )
        elif version_kind == 'testing':
            url = '{protocol}://download.ceph.com/debian-testing/'.format(
                protocol=protocol,
                )
        elif version_kind in ['dev', 'dev_commit']:
            url = 'http://gitbuilder.ceph.com/ceph-deb-{codename}-{machine}-basic/{sub}/{version}'.format(
                codename=codename,
                machine=machine,
                sub='ref' if version_kind == 'dev' else 'sha1',
                version=version,
                )
        else:
            raise RuntimeError('Unknown version kind: %r' % version_kind)

        # set the repo priority for the right domain
        fqdn = urlparse(url).hostname
        distro.conn.remote_module.set_apt_priority(fqdn)
        distro.conn.remote_module.write_sources_list(url, codename)

    distro.packager.clean()

    # TODO this does not downgrade -- should it?
    if packages:
        distro.packager.install(
            packages,
            extra_install_flags=['-o', 'Dpkg::Options::=--force-confnew']
        )


def mirror_install(distro, repo_url, gpg_url, adjust_repos, **kw):
    packages = map_components(
        NON_SPLIT_COMPONENTS,
        kw.pop('components', [])
    )
    repo_url = repo_url.strip('/')  # Remove trailing slashes

    if adjust_repos:
        distro.packager.add_repo_gpg_key(gpg_url)

        # set the repo priority for the right domain
        fqdn = urlparse(repo_url).hostname
        distro.conn.remote_module.set_apt_priority(fqdn)

        distro.conn.remote_module.write_sources_list(repo_url, distro.codename)

    if packages:
        distro.packager.clean()
        distro.packager.install(packages)


def repo_install(distro, repo_name, baseurl, gpgkey, **kw):
    packages = map_components(
        NON_SPLIT_COMPONENTS,
        kw.pop('components', [])
    )
    # Get some defaults
    safe_filename = '%s.list' % repo_name.replace(' ', '-')
    install_ceph = kw.pop('install_ceph', False)
    baseurl = baseurl.strip('/')  # Remove trailing slashes

    distro.packager.add_repo_gpg_key(gpgkey)

    distro.conn.remote_module.write_sources_list(
        baseurl,
        distro.codename,
        safe_filename
    )

    # set the repo priority for the right domain
    fqdn = urlparse(baseurl).hostname
    distro.conn.remote_module.set_apt_priority(fqdn)

    # repo is not operable until an update
    distro.packager.clean()

    if install_ceph and packages:
        distro.packager.install(packages)
