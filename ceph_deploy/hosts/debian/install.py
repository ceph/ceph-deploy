from ceph_deploy.lib import remoto
from ceph_deploy.util import pkg_managers


def install(distro, version_kind, version, adjust_repos):
    codename = distro.codename
    machine = distro.machine_type

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    # Make sure ca-certificates is installed
    remoto.process.run(
        distro.conn,
        [
            'env',
            'DEBIAN_FRONTEND=noninteractive',
            'apt-get',
            '-q',
            'install',
            '--assume-yes',
            'ca-certificates',
        ]
    )

    if adjust_repos:
        remoto.process.run(
            distro.conn,
            [
                'wget',
                '-O',
                '{key}.asc'.format(key=key),
                'https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc'.format(key=key),
            ],
            stop_on_nonzero=False,
        )

        remoto.process.run(
            distro.conn,
            [
                'apt-key',
                'add',
                '{key}.asc'.format(key=key)
            ]
        )

        if version_kind == 'stable':
            url = 'http://ceph.com/debian-{version}/'.format(
                version=version,
                )
        elif version_kind == 'testing':
            url = 'http://ceph.com/debian-testing/'
        elif version_kind == 'dev':
            url = 'http://gitbuilder.ceph.com/ceph-deb-{codename}-{machine}-basic/ref/{version}'.format(
                codename=codename,
                machine=machine,
                version=version,
                )
        else:
            raise RuntimeError('Unknown version kind: %r' % version_kind)

        distro.conn.remote_module.write_sources_list(url, codename)

    remoto.process.run(
        distro.conn,
        ['apt-get', '-q', 'update'],
        )

    # TODO this does not downgrade -- should it?
    remoto.process.run(
        distro.conn,
        [
            'env',
            'DEBIAN_FRONTEND=noninteractive',
            'DEBIAN_PRIORITY=critical',
            'apt-get',
            '-q',
            '-o', 'Dpkg::Options::=--force-confnew',
            '--no-install-recommends',
            '--assume-yes',
            'install',
            '--',
            'ceph',
            'ceph-mds',
            'ceph-common',
            'ceph-fs-common',
            # ceph only recommends gdisk, make sure we actually have
            # it; only really needed for osds, but minimal collateral
            'gdisk',
            ],
        )


def mirror_install(distro, repo_url, gpg_url, adjust_repos):
    repo_url = repo_url.strip('/')  # Remove trailing slashes
    gpg_path = gpg_url.split('file://')[-1]

    if adjust_repos:
        if not gpg_url.startswith('file://'):
            remoto.process.run(
                distro.conn,
                [
                    'wget',
                    '-O',
                    'release.asc',
                    gpg_url,
                ],
                stop_on_nonzero=False,
            )

        gpg_file = 'release.asc' if not gpg_url.startswith('file://') else gpg_path
        remoto.process.run(
            distro.conn,
            [
                'apt-key',
                'add',
                gpg_file,
            ]
        )

        distro.conn.remote_module.write_sources_list(repo_url, distro.codename)

    # Before any install, make sure we have `wget`
    pkg_managers.apt_update(distro.conn)
    packages = (
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        # ceph only recommends gdisk, make sure we actually have
        # it; only really needed for osds, but minimal collateral
        'gdisk',
    )

    pkg_managers.apt(distro.conn, packages)
    pkg_managers.apt(distro.conn, 'ceph')


def repo_install(distro, repo_name, baseurl, gpgkey, **kw):
    # Get some defaults
    safe_filename = '%s.list' % repo_name.replace(' ', '-')
    install_ceph = kw.pop('install_ceph', False)
    baseurl = baseurl.strip('/')  # Remove trailing slashes

    if gpgkey:
        remoto.process.run(
            distro.conn,
            [
                'wget',
                '-O',
                'release.asc',
                gpgkey,
            ],
            stop_on_nonzero=False,
        )

    remoto.process.run(
        distro.conn,
        [
            'apt-key',
            'add',
            'release.asc'
        ]
    )

    distro.conn.remote_module.write_sources_list(
        baseurl,
        distro.codename,
        safe_filename
    )

    # repo is not operable until an update
    pkg_managers.apt_update(distro.conn)

    if install_ceph:
        # Before any install, make sure we have `wget`
        packages = (
            'ceph',
            'ceph-mds',
            'ceph-common',
            'ceph-fs-common',
            # ceph only recommends gdisk, make sure we actually have
            # it; only really needed for osds, but minimal collateral
            'gdisk',
        )

        pkg_managers.apt(distro.conn, packages)
        pkg_managers.apt(distro.conn, 'ceph')
