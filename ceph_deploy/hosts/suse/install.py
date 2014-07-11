from ceph_deploy.util import templates, pkg_managers
from ceph_deploy.lib import remoto
import logging
LOG = logging.getLogger(__name__)


def install(distro, version_kind, version, adjust_repos):
    release = distro.release
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'


    distro_name = None
    if distro.codename == 'Mantis':
        distro_name = 'opensuse12.2'

    if (distro.name == "SUSE Linux Enterprise Server") and (str(distro.release) == "11"):
        distro_name = 'sles11'

    if distro_name == None:
        LOG.warning('Untested version of %s: assuming compatible with SUSE Linux Enterprise Server 11', distro.name)
        distro_name = 'sles11'


    if adjust_repos:
        # Work around code due to bug in SLE 11
        # https://bugzilla.novell.com/show_bug.cgi?id=875170
        protocol = "https"
        if distro_name == 'sles11':
            protocol = "http"
        remoto.process.run(
            distro.conn,
            [
                'rpm',
                '--import',
                "{protocol}://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc".format(
                    key=key,
                    protocol=protocol)
            ]
        )

        if version_kind == 'stable':
            url = 'http://ceph.com/rpm-{version}/{distro}/'.format(
                version=version,
                distro=distro_name,
                )
        elif version_kind == 'testing':
            url = 'http://ceph.com/rpm-testing/{distro}/'.format(distro=distro_name)
        elif version_kind == 'dev':
            url = 'http://gitbuilder.ceph.com/ceph-rpm-{distro}{release}-{machine}-basic/ref/{version}/'.format(
                distro=distro_name,
                release=release.split(".", 1)[0],
                machine=machine,
                version=version,
                )

        remoto.process.run(
            distro.conn,
            [
                'rpm',
                '-Uvh',
                '--replacepkgs',
                '--force',
                '--quiet',
                '{url}ceph-release-1-0.noarch.rpm'.format(
                    url=url,
                    ),
                ]
            )

    remoto.process.run(
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

    remoto.process.run(
        distro.conn,
        [
            'zypper',
            '--non-interactive',
            '--quiet',
            'install',
            'ceph',
            ],
        )


def repo_install(distro, reponame, baseurl, gpgkey, **kw):
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
    if install_ceph:
        # Before any install, make sure we have `wget`
        pkg_managers.zypper(distro.conn, 'wget')

        pkg_managers.zypper(distro.conn, 'ceph')
