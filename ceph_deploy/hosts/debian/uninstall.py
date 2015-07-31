def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        'radosgw',
        ]
    distro.packager.remove(
        packages,
        purge=purge,
    )
