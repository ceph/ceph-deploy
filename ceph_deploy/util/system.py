from ceph_deploy.exc import ExecutableNotFound


def executable_path(conn, executable):
    """
    Remote validator that accepts a connection object to ensure that a certain
    executable is available returning its full path if so.

    Otherwise an exception with thorough details will be raised, informing the
    user that the executable was not found.
    """
    executable_path = conn.remote_module.which(executable)
    if not executable_path:
        raise ExecutableNotFound(executable, conn.hostname)
    return executable_path
