def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-common',
        'ceph-radosgw',
        ]

    distro.packager.remove(packages)
