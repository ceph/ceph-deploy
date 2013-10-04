from ceph_deploy.lib.remoto import Connection
from sudo_pushy import needs_sudo  # TODO move this to utils once pushy is out


def get_connection(hostname, logger, threads=5):
    """
    A very simple helper, meant to return a connection
    that will know about the need to use sudo.
    """
    try:
        return Connection(
            hostname,
            logger=logger,
            sudo=needs_sudo(),
            threads=threads,
        )

    except Exception as error:
        msg = "connecting to host: %s " % hostname
        errors = "resulted in errors: %s %s" % (error.__class__.__name__, error)
        raise RuntimeError(msg + errors)
