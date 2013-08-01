from ceph_deploy.util.wrappers import check_call
from ceph_deploy.hosts import common


def install(distro, logger, version_kind, version):
    release = distro.release
    machine = distro.sudo_conn.modules.platform.machine()

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    check_call(
        distro.sudo_conn,
        logger,
        ['su -c \'rpm --import "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc"\''.format(key=key),],
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

    check_call(
        distro.sudo_conn,
        logger,
        [
            'rpm',
            '-Uvh',
            '--replacepkgs',
            '--force',
            '--quiet',
            '{url}noarch/ceph-release-1-0.el6.noarch.rpm'.format(url=url),
        ],
    )

    check_call(
        distro.sudo_conn,
        logger,
        [
            'yum',
            '-y',
            '-q',
            'install',
            'ceph',
        ],
    )

    # Check the ceph version
    common.ceph_version(distro.sudo_conn, logger)
