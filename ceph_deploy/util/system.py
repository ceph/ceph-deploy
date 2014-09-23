from ceph_deploy.exc import ExecutableNotFound
from ceph_deploy.lib import remoto


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


def is_systemd(conn):
    """
    Attempt to detect if a remote system is a systemd one or not
    by looking into ``/proc`` just like the ceph init script does::

        # detect systemd
        # SYSTEMD=0
        grep -qs systemd /proc/1/comm && SYSTEMD=1
    """
    return conn.remote_module.grep(
        'systemd',
        '/proc/1/comm'
    )


def enable_service(conn, service='ceph'):
    """
    Enable a service on a remote host depending on the type of init system.
    Obviously, this should be done for RHEL/Fedora/CentOS systems.

    This function does not do any kind of detection.
    """
    if is_systemd(conn):
        remoto.process.run(
            conn,
            [
                'systemctl',
                'enable',
                'ceph',
            ]
        )
    else:
        remoto.process.run(
            conn,
            [
                'chkconfig',
                'ceph',
                'on',
            ]
        )
