import getpass
from ceph_deploy.lib.remoto import Connection


def get_connection(hostname, username, logger, threads=5):
    """
    A very simple helper, meant to return a connection
    that will know about the need to use sudo.
    """
    if username:
        hostname = "%s@%s" % (username, hostname)
    try:
        conn = Connection(
            hostname,
            logger=logger,
            sudo=needs_sudo(),
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


def needs_sudo():
    if getpass.getuser() == 'root':
        return False
    return True
