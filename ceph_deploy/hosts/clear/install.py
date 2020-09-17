
def install(distro, version_kind, version, adjust_repos, **kw):
    """
    Install bundle that contains ceph on the clear host.

    Since clear does not have alternate channels, we will just run the command
    """
    logger = distro.conn.logger
    packages = ['storage-cluster']

    logger.info("Installing storage-cluster bundle")
    distro.packager.install(
        packages
        )
