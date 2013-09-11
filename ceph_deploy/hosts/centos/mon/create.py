from ceph_deploy.util.wrappers import check_call
from ceph_deploy.hosts import common
from ceph_deploy.misc import remote_shortname


def create(distro, logger, args, monitor_keyring):
    hostname = remote_shortname(distro.sudo_conn.modules.socket)
    common.mon_create(distro, logger, args, monitor_keyring, hostname)
    service = common.which_service(distro.sudo_conn, logger)
    check_call(
        distro.sudo_conn,
        logger,
        [
            service,
            'ceph',
            'start',
            'mon.{hostname}'.format(hostname=hostname)
        ],
        patch=False,
    )
