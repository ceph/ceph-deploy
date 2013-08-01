from ceph_deploy.util import wrappers


def ceph_version(conn, logger):
    """
    Log the remote ceph-version by calling `ceph --version`
    """
    return wrappers.check_call(conn, logger, ['ceph', '--version'])
