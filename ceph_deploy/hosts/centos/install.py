

def install(release, codename, version_kind, version):
    import platform
    import subprocess

    if version_kind in ['stable', 'testing']:
        key = 'release'
    else:
        key = 'autobuild'

    subprocess.check_call(
        args='su -c \'rpm --import "https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/{key}.asc"\''.format(key=key),
        shell=True,
        )

    if version_kind == 'stable':
        url = 'http://ceph.com/rpm-{version}/el6/'.format(
            version=version,
            )
    elif version_kind == 'testing':
        url = 'http://ceph.com/rpm-testing/'
    elif version_kind == 'dev':
        url = 'http://gitbuilder.ceph.com/ceph-rpm-centos{release}-{machine}-basic/ref/{version}/'.format(
            release=release.split(".",1)[0],
            machine=platform.machine(),
            version=version,
            )

    subprocess.check_call(
        args=[
            'rpm',
            '-Uvh',
            '--replacepkgs',
            '--force',
            '--quiet',
            '{url}noarch/ceph-release-1-0.el6.noarch.rpm'.format(
                url=url,
                ),
            ]
        )

    subprocess.check_call(
        args=[
            'yum',
            '-y',
            '-q',
            'install',
            'ceph',
            ],
        )
