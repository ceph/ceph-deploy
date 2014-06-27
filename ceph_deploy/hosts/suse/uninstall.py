from ceph_deploy.lib import remoto


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
    remoto.process.run(conn, cmd)
