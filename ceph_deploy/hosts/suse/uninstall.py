def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-common',
        'libcephfs1',
        'librados2',
        'librbd1',
        'ceph-radosgw',
        ]
    distro.packager.remove(packages)
