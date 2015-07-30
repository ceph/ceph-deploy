def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-release',
        'ceph-common',
        'ceph-radosgw',
        ]

    distro.packager.remove(packages)
    distro.packager.clean()
