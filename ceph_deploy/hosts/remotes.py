import errno
import socket
import os
import tempfile
import platform


def platform_information():
    """ detect platform information from remote host """
    distro, release, codename = platform.linux_distribution()
    return (
        str(distro).rstrip(),
        str(release).rstrip(),
        str(codename).rstrip()
    )


def machine_type():
    """ detect machine type """
    return platform.machine()


def write_sources_list(url, codename):
    """add ceph deb repo to sources.list"""
    with file('/etc/apt/sources.list.d/ceph.list', 'w') as f:
        f.write('deb {url} {codename} main\n'.format(
                url=url,
                codename=codename,
                ))


def write_conf(cluster, conf, overwrite):
    """ write cluster configuration to /etc/ceph/{cluster}.conf """
    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    err_msg = 'config file %s exists with different content; use --overwrite-conf to overwrite' % path

    if os.path.exists(path):
        with file(path, 'rb') as f:
            old = f.read()
            if old != conf and not overwrite:
                raise RuntimeError(err_msg)
    tmp_file.write(conf)
    os.rename(tmp_file.name, path)


def create_mon_path(path):
    """create the mon path if it does not exist"""
    if not os.path.exists(path):
        os.makedirs(path)


def create_done_path(done_path):
    """create a done file to avoid re-doing the mon deployment"""
    with file(done_path, 'w'):
        pass


def create_init_path(init_path):
    """create the init path if it does not exist"""
    if not os.path.exists(init_path):
        with file(init_path, 'w'):
            pass


def path_exists(path):
    return os.path.exists(path)


def makedir(path):
    os.makedirs(path)


def unlink(_file):
    os.unlink(_file)


def write_monitor_keyring(keyring, monitor_keyring):
    """create the monitor keyring file"""
    with file(keyring, 'w') as f:
        f.write(monitor_keyring)


def shortname():
    """get remote short hostname"""
    return socket.gethostname().split('.', 1)[0]


def which_service():
    """ locating the `service` executable... """
    locations = ['/sbin/service', '/usr/sbin/service']
    for location in locations:
        if os.path.exists(location):
            return location


def make_mon_removed_dir(path, file_name):
    """ move old monitor data """
    try:
        os.makedirs('/var/lib/ceph/mon-removed')
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
    os.rename(path, os.path.join('/var/lib/ceph/mon-removed/', file_name))


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
