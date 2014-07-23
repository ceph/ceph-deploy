import logging
from ceph_deploy.lib import remoto
from ceph_deploy.connection import get_local_connection


def can_connect_passwordless(hostname):
    """
    Ensure that current host can SSH remotely to the remote
    host using the ``BatchMode`` option to prevent a password prompt.

    That attempt will error with an exit status of 255 and a ``Permission
    denied`` message or a``Host key verification failed`` message.
    """
    # Ensure we are not doing this for local hosts
    if not remoto.connection.needs_ssh(hostname):
        return True

    logger = logging.getLogger(hostname)
    with get_local_connection(logger) as conn:
        # Check to see if we can login, disabling password prompts
        command = ['ssh', '-CT', '-o', 'BatchMode=yes', hostname]
        out, err, retval = remoto.process.check(conn, command, stop_on_error=False)
        permission_denied_error = 'Permission denied '
        host_key_verify_error = 'Host key verification failed.'
        has_key_error = False
        for line in err:
            if permission_denied_error in line or host_key_verify_error in line:
                has_key_error = True

        if retval == 255 and has_key_error:
            return False
    return True
