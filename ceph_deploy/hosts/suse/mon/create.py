from ceph_deploy.hosts import common
from ceph_deploy.misc import remote_shortname
from ceph_deploy.lib.remoto import Connection, process


def create(distro, logger, args, monitor_keyring):
    hostname = remote_shortname(distro.sudo_conn.modules.socket)
    common.mon_create(distro, logger, args, monitor_keyring, hostname)
    service = common.which_service(distro.sudo_conn, logger)

    # TODO transition this once pushy is out
    rconn = Connection(hostname, logger, sudo=True)

    process.run(
        rconn,
        [
            service,
            'ceph',
            'start',
            'mon.{hostname}'.format(hostname=hostname)
        ],
        exit=True,
    )
