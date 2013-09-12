from ceph_deploy.lib.remoto import Connection
from sudo_pushy import needs_sudo  # TODO move this to utils once pushy is out


def get_connection(hostname, logger):
    """
    A very simple helper, meant to return a connection
    that will know about the need to use sudo.
    """
    return Connection(
        hostname,
        logger=logger,
        sudo=needs_sudo(),
    )
