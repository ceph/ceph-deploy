import errno
import socket
import os
import shutil
import tempfile
import platform


def platform_information():
    """ detect platform information from remote host """
    distro, release, codename = platform.linux_distribution()
    if not codename and 'debian' in distro.lower():  # this could be an empty string in Debian
        debian_codenames = {
            '8': 'jessie',
            '7': 'wheezy',
            '6': 'squeeze',
        }
        major_version = release.split('.')[0]
        codename = debian_codenames.get(major_version, '')

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
        tmp_file.close()
        shutil.move(tmp_file.name, path)
        return
    if os.path.exists('/etc/ceph'):
        with open(path, 'w') as f:
            f.write(conf)
    else:
        err_msg = '/etc/ceph/ does not exist - could not write config'
        raise RuntimeError(err_msg)


def write_keyring(path, key):
    """ create a keyring file """
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(key)
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


def append_to_file(file_path, contents):
    """append contents to file"""
    with open(file_path, 'a') as f:
        f.write(contents)


def path_exists(path):
    return os.path.exists(path)


def makedir(path):
    os.makedirs(path)


def unlink(_file):
    os.unlink(_file)


def write_monitor_keyring(keyring, monitor_keyring):
    """create the monitor keyring file"""
    write_file(keyring, monitor_keyring)


def write_file(path, content):
    with file(path, 'w') as f:
        f.write(content)


def touch_file(path):
    with file(path, 'wb') as f:  # noqa
        pass


def get_file(path):
    """ fetch remote file """
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        pass


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


def safe_mkdir(path):
    """ create path if it doesn't exist """
    try:
        os.mkdir(path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


def zeroing(dev):
    """ zeroing last few blocks of device """
    # this kills the crab
    #
    # sgdisk will wipe out the main copy of the GPT partition
    # table (sorry), but it doesn't remove the backup copies, and
    # subsequent commands will continue to complain and fail when
    # they see those.  zeroing the last few blocks of the device
    # appears to do the trick.
    lba_size = 4096
    size = 33 * lba_size
    return True
    with file(dev, 'wb') as f:
        f.seek(-size, os.SEEK_END)
        f.write(size*'\0')


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
