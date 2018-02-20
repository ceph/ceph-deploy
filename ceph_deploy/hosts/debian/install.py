try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import logging
from ceph_deploy.util.paths import gpg
from ceph_deploy.util import net


LOG = logging.getLogger(__name__)


def install(distro, version_kind, version, adjust_repos, **kw):
    packages = kw.pop('components', [])
    codename = distro.codename
    machine = distro.machine_type
    extra_install_flags = []

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    distro.packager.clean()
    distro.packager.install(['ca-certificates', 'apt-transport-https'])

    if adjust_repos:
        # Wheezy does not like the download.ceph.com SSL cert
        protocol = 'https'
        if codename == 'wheezy':
            protocol = 'http'

        if version_kind in ['dev', 'dev_commit']:
            shaman_url = 'https://shaman.ceph.com/api/repos/ceph/{version}/{sha1}/{distro}/{distro_version}/repo/?arch={arch}'.format(
                distro=distro.normalized_name,
                distro_version=distro.codename,
                version=kw['args'].dev,
                sha1=kw['args'].dev_commit or 'latest',
                arch=machine
                )
            LOG.debug('fetching repo information from: %s' % shaman_url)
            chacra_url = net.get_request(shaman_url).geturl()
            content = net.get_chacra_repo(shaman_url)
            # set the repo priority for the right domain
            fqdn = urlparse(chacra_url).hostname
            distro.conn.remote_module.set_apt_priority(fqdn)
            distro.conn.remote_module.write_sources_list_content(content)
            extra_install_flags = ['-o', 'Dpkg::Options::=--force-confnew', '--allow-unauthenticated']
        else:
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
            else:
                raise RuntimeError('Unknown version kind: %r' % version_kind)

            # set the repo priority for the right domain
            fqdn = urlparse(url).hostname
            distro.conn.remote_module.set_apt_priority(fqdn)
            distro.conn.remote_module.write_sources_list(url, codename)
            extra_install_flags = ['-o', 'Dpkg::Options::=--force-confnew']

    distro.packager.clean()

    # TODO this does not downgrade -- should it?
    if packages:
        distro.packager.install(
            packages,
            extra_install_flags=extra_install_flags
        )


def mirror_install(distro, repo_url, gpg_url, adjust_repos, **kw):
    packages = kw.pop('components', [])
    version_kind = kw['args'].version_kind
    repo_url = repo_url.strip('/')  # Remove trailing slashes

    if adjust_repos:
        distro.packager.add_repo_gpg_key(gpg_url)

        # set the repo priority for the right domain
        fqdn = urlparse(repo_url).hostname
        distro.conn.remote_module.set_apt_priority(fqdn)

        distro.conn.remote_module.write_sources_list(repo_url, distro.codename)

    extra_install_flags = ['--allow-unauthenticated'] if version_kind in 'dev' else []

    if packages:
        distro.packager.clean()
        distro.packager.install(
            packages,
            extra_install_flags=extra_install_flags)


def repo_install(distro, repo_name, baseurl, gpgkey, **kw):
    packages = kw.pop('components', [])
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
