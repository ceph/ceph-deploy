def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-common',
        'ceph-mon',
        'ceph-osd',
        'ceph-radosgw'
        ]

    distro.packager.remove(packages)
    distro.packager.clean()
