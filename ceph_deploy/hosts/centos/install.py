from ceph_deploy.util.wrappers import check_call


def install(distro, logger, version_kind, version):
    release = distro.release
    machine = distro.sudo_conn.modules.platform.machine()

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    check_call([
        'su -c \'rpm --import "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc"\''.format(key=key),],
        logger,
        distro.sudo_conn,
        shell=True)

    if version_kind == 'stable':
        url = 'http://ceph.com/rpm-{version}/el6/'.format(
            version=version,
            )
    elif version_kind == 'testing':
        url = 'http://ceph.com/rpm-testing/'
    elif version_kind == 'dev':
        url = 'http://gitbuilder.ceph.com/ceph-rpm-centos{release}-{machine}-basic/ref/{version}/'.format(
            release=release.split(".",1)[0],
            machine=machine,
            version=version,
            )

    check_call([
        'rpm',
        '-Uvh',
        '--replacepkgs',
        '--force',
        '--quiet',
        '{url}noarch/ceph-release-1-0.el6.noarch.rpm'.format(url=url),
        ],
        logger,
        distro.sudo_conn
    )

    check_call([
        'yum',
        '-y',
        '-q',
        'install',
        'ceph',
        ],
        logger,
        distro.sudo_conn
    )
