def uninstall(distro, purge=False):
    packages = [
        'ceph-common',
        'ceph-base',
        'ceph-radosgw',
        'python-module-cephfs',
        'python-module-rados',
        'python-module-rbd',
        'python-module-rgw',
        ]
    distro.packager.remove(packages)
