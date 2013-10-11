from ceph_deploy.lib.remoto import process


def uninstall(conn, purge=False):
    packages = [
        'ceph',
        'libcephfs1',
        'librados2',
        'librbd1',
        ]
    cmd = [
        'zypper',
        '--non-interactive',
        '--quiet',
        'remove',
        ]

    cmd.extend(packages)
    process.run(conn, cmd)
