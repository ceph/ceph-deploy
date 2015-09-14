from ceph_deploy.hosts import common


def create(distro, args, monitor_keyring):
    hostname = distro.conn.remote_module.shortname()
    common.mon_create(distro, args, monitor_keyring, hostname)

    distro.init.start('ceph-mon')
    distro.init.enable('ceph-mon')
