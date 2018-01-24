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


def is_upstart(conn):
    """
    This helper should only used as a fallback (last resort) as it is not
    guaranteed that it will be absolutely correct.
    """
    # it may be possible that we may be systemd and the caller never checked
    # before so lets do that
    if is_systemd(conn):
        return False

    # get the initctl executable, if it doesn't exist we can't proceed so we
    # are probably not upstart
    initctl = conn.remote_module.which('initctl')
    if not initctl:
        return False

    # finally, try and get output from initctl that might hint this is an upstart
    # system. On a Ubuntu 14.04.2 system this would look like:
    # $ initctl version
    # init (upstart 1.12.1)
    stdout, stderr, _ = remoto.process.check(
        conn,
        [initctl, 'version'],
    )
    result_string = b' '.join(stdout)
    if b'upstart' in result_string:
        return True
    return False


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
                '{service}'.format(service=service),
            ]
        )
    else:
        remoto.process.run(
            conn,
            [
                'chkconfig',
                '{service}'.format(service=service),
                'on',
            ]
        )


def disable_service(conn, service='ceph'):
    """
    Disable a service on a remote host depending on the type of init system.
    Obviously, this should be done for RHEL/Fedora/CentOS systems.

    This function does not do any kind of detection.
    """
    if is_systemd(conn):
        # Without the check, an error is raised trying to disable an
        # already disabled service
        if is_systemd_service_enabled(conn, service):
            remoto.process.run(
                conn,
                [
                    'systemctl',
                    'disable',
                    '{service}'.format(service=service),
                ]
            )


def stop_service(conn, service='ceph'):
    """
    Stop a service on a remote host depending on the type of init system.
    Obviously, this should be done for RHEL/Fedora/CentOS systems.

    This function does not do any kind of detection.
    """
    if is_systemd(conn):
        # Without the check, an error is raised trying to stop an
        # already stopped service
        if is_systemd_service_active(conn, service):
            remoto.process.run(
                conn,
                [
                    'systemctl',
                    'stop',
                    '{service}'.format(service=service),
                ]
            )


def start_service(conn, service='ceph'):
    """
    Stop a service on a remote host depending on the type of init system.
    Obviously, this should be done for RHEL/Fedora/CentOS systems.

    This function does not do any kind of detection.
    """
    if is_systemd(conn):
        remoto.process.run(
            conn,
            [
                'systemctl',
                'start',
                '{service}'.format(service=service),
            ]
        )


def is_systemd_service_active(conn, service='ceph'):
    """
    Detects if a systemd service is active or not.
    """
    _, _, returncode = remoto.process.check(
        conn,
        [
            'systemctl',
            'is-active',
            '--quiet',
            '{service}'.format(service=service),
        ]
    )
    return returncode == 0


def is_systemd_service_enabled(conn, service='ceph'):
    """
    Detects if a systemd service is enabled or not.
    """
    _, _, returncode = remoto.process.check(
        conn,
        [
            'systemctl',
            'is-enabled',
            '--quiet',
            '{service}'.format(service=service),
        ]
    )
    return returncode == 0
