def uninstall(distro, purge=False):
    packages = [
        'ceph',
        'ceph-mds',
        'ceph-common',
        'ceph-fs-common',
        'radosgw',
        ]
    extra_remove_flags = []
    if purge:
        extra_remove_flags.append('--purge')
    distro.packager.remove(
        packages,
        extra_remove_flags=extra_remove_flags
    )
