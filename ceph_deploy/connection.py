import getpass
import socket
from ceph_deploy.lib.remoto import Connection


def get_connection(hostname, username, logger, threads=5, use_sudo=None):
    """
    A very simple helper, meant to return a connection
    that will know about the need to use sudo.
    """
    if use_sudo is None:
        use_sudo = needs_sudo()
    if username:
        hostname = "%s@%s" % (username, hostname)
    try:
        conn = Connection(
            hostname,
            logger=logger,
            sudo=use_sudo,
            threads=threads,
        )

        # Set a timeout value in seconds to disconnect and move on
        # if no data is sent back.
        conn.global_timeout = 300
        logger.debug("connected to host: %s " % hostname)
        return conn

    except Exception as error:
        msg = "connecting to host: %s " % hostname
        errors = "resulted in errors: %s %s" % (error.__class__.__name__, error)
        raise RuntimeError(msg + errors)


def get_local_connection(logger, use_sudo=False):
    """
    Helper for local connections that are sometimes needed to operate
    on local hosts
    """
    return get_connection(
        socket.gethostname(),  # cannot rely on 'localhost' here
        None,
        logger=logger,
        threads=1,
        use_sudo=use_sudo
    )


def needs_sudo():
    if getpass.getuser() == 'root':
        return False
    return True
