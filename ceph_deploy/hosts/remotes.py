try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import errno
import socket
import os
import shutil
import tempfile
import platform


def platform_information(_linux_distribution=None):
    """ detect platform information from remote host """
    linux_distribution = _linux_distribution or platform.linux_distribution
    distro, release, codename = linux_distribution()
    if not codename and 'debian' in distro.lower():  # this could be an empty string in Debian
        debian_codenames = {
            '8': 'jessie',
            '7': 'wheezy',
            '6': 'squeeze',
        }
        major_version = release.split('.')[0]
        codename = debian_codenames.get(major_version, '')

        # In order to support newer jessie/sid or wheezy/sid strings we test this
        # if sid is buried in the minor, we should use sid anyway.
        if not codename and '/' in release:
            major, minor = release.split('/')
            if minor == 'sid':
                codename = minor
            else:
                codename = major

    return (
        str(distro).rstrip(),
        str(release).rstrip(),
        str(codename).rstrip()
    )


def machine_type():
    """ detect machine type """
    return platform.machine()


def write_sources_list(url, codename, filename='ceph.list', mode=0o644):
    """add deb repo to /etc/apt/sources.list.d/"""
    repo_path = os.path.join('/etc/apt/sources.list.d', filename)
    content = 'deb {url} {codename} main\n'.format(
        url=url,
        codename=codename,
    )
    write_file(repo_path, content.encode('utf-8'), mode)


def write_yum_repo(content, filename='ceph.repo'):
    """add yum repo file in /etc/yum.repos.d/"""
    repo_path = os.path.join('/etc/yum.repos.d', filename)
    write_file(repo_path, content.encode('utf-8'))


def set_apt_priority(fqdn, path='/etc/apt/preferences.d/ceph.pref'):
    template = "Package: *\nPin: origin {fqdn}\nPin-Priority: 999\n"
    content = template.format(fqdn=fqdn)
    with open(path, 'w') as fout:
        fout.write(content)


def set_repo_priority(sections, path='/etc/yum.repos.d/ceph.repo', priority='1'):
    Config = configparser.ConfigParser()
    Config.read(path)
    Config.sections()
    for section in sections:
        try:
            Config.set(section, 'priority', priority)
        except configparser.NoSectionError:
            # Emperor versions of Ceph used all lowercase sections
            # so lets just try again for the section that failed, maybe
            # we are able to find it if it is lower
            Config.set(section.lower(), 'priority', priority)

    with open(path, 'w') as fout:
        Config.write(fout)

    # And now, because ConfigParser is super duper, we need to remove the
    # assignments so this looks like it was before
    def remove_whitespace_from_assignments():
        separator = "="
        lines = open(path).readlines()
        fp = open(path, "w")
        for line in lines:
            line = line.strip()
            if not line.startswith("#") and separator in line:
                assignment = line.split(separator, 1)
                assignment = tuple(map(str.strip, assignment))
                fp.write("%s%s%s\n" % (assignment[0], separator, assignment[1]))
            else:
                fp.write(line + "\n")

    remove_whitespace_from_assignments()


def write_conf(cluster, conf, overwrite):
    """ write cluster configuration to /etc/ceph/{cluster}.conf """
    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp_file = tempfile.NamedTemporaryFile('w', dir='/etc/ceph', delete=False)
    err_msg = 'config file %s exists with different content; use --overwrite-conf to overwrite' % path

    if os.path.exists(path):
        with open(path, 'r') as f:
            old = f.read()
            if old != conf and not overwrite:
                raise RuntimeError(err_msg)
        tmp_file.write(conf)
        tmp_file.close()
        shutil.move(tmp_file.name, path)
        os.chmod(path, 0o644)
        return
    if os.path.exists('/etc/ceph'):
        with open(path, 'w') as f:
            f.write(conf)
        os.chmod(path, 0o644)
    else:
        err_msg = '/etc/ceph/ does not exist - could not write config'
        raise RuntimeError(err_msg)


def write_keyring(path, key, uid=-1, gid=-1):
    """ create a keyring file """
    # Note that we *require* to avoid deletion of the temp file
    # otherwise we risk not being able to copy the contents from
    # one file system to the other, hence the `delete=False`
    tmp_file = tempfile.NamedTemporaryFile('wb', delete=False)
    tmp_file.write(key)
    tmp_file.close()
    keyring_dir = os.path.dirname(path)
    if not path_exists(keyring_dir):
        makedir(keyring_dir, uid, gid)
    shutil.move(tmp_file.name, path)


def create_mon_path(path, uid=-1, gid=-1):
    """create the mon path if it does not exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        os.chown(path, uid, gid);


def create_done_path(done_path, uid=-1, gid=-1):
    """create a done file to avoid re-doing the mon deployment"""
    with open(done_path, 'wb'):
        pass
    os.chown(done_path, uid, gid);


def create_init_path(init_path, uid=-1, gid=-1):
    """create the init path if it does not exist"""
    if not os.path.exists(init_path):
        with open(init_path, 'wb'):
            pass
        os.chown(init_path, uid, gid);


def append_to_file(file_path, contents):
    """append contents to file"""
    with open(file_path, 'a') as f:
        f.write(contents)

def path_getuid(path):
    return os.stat(path).st_uid

def path_getgid(path):
    return os.stat(path).st_gid

def readline(path):
    with open(path) as _file:
        return _file.readline().strip('\n')


def path_exists(path):
    return os.path.exists(path)


def get_realpath(path):
    return os.path.realpath(path)


def listdir(path):
    return os.listdir(path)


def makedir(path, ignored=None, uid=-1, gid=-1):
    ignored = ignored or []
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno in ignored:
            pass
        else:
            # re-raise the original exception
            raise
    else:
        os.chown(path, uid, gid);


def unlink(_file):
    os.unlink(_file)


def write_monitor_keyring(keyring, monitor_keyring, uid=-1, gid=-1):
    """create the monitor keyring file"""
    write_file(keyring, monitor_keyring, 0o600, None, uid, gid)


def write_file(path, content, mode=0o644, directory=None, uid=-1, gid=-1):
    if directory:
        if path.startswith("/"):
            path = path[1:]
        path = os.path.join(directory, path)
    if os.path.exists(path):
        # Delete file in case we are changing its mode
        os.unlink(path)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT, mode), 'wb') as f:
        f.write(content)
    os.chown(path, uid, gid)


def touch_file(path):
    with open(path, 'wb') as f:  # noqa
        pass


def get_file(path):
    """ fetch remote file """
    try:
        with open(path, 'rb') as f:
            return f.read()
    except IOError:
        pass


def object_grep(term, file_object):
    for line in file_object.readlines():
        if term in line:
            return True
    return False


def grep(term, file_path):
    # A small grep-like function that will search for a word in a file and
    # return True if it does and False if it does not.

    # Implemented initially to have a similar behavior as the init system
    # detection in Ceph's init scripts::

    #     # detect systemd
    #     # SYSTEMD=0
    #     grep -qs systemd /proc/1/comm && SYSTEMD=1

    # .. note:: Because we intent to be operating in silent mode, we explicitly
    # return ``False`` if the file does not exist.
    if not os.path.isfile(file_path):
        return False

    with open(file_path) as _file:
        return object_grep(term, _file)


def shortname():
    """get remote short hostname"""
    return socket.gethostname().split('.', 1)[0]


def which_service():
    """ locating the `service` executable... """
    # XXX This should get deprecated at some point. For now
    # it just bypasses and uses the new helper.
    return which('service')


def which(executable):
    """find the location of an executable"""
    locations = (
        '/usr/local/bin',
        '/bin',
        '/usr/bin',
        '/usr/local/sbin',
        '/usr/sbin',
        '/sbin',
    )

    for location in locations:
        executable_path = os.path.join(location, executable)
        if os.path.exists(executable_path):
            return executable_path


def make_mon_removed_dir(path, file_name):
    """ move old monitor data """
    try:
        os.makedirs('/var/lib/ceph/mon-removed')
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    shutil.move(path, os.path.join('/var/lib/ceph/mon-removed/', file_name))


def safe_mkdir(path, uid=-1, gid=-1):
    """ create path if it doesn't exist """
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        os.chown(path, uid, gid)

def safe_makedirs(path, uid=-1, gid=-1):
    """ create path recursively if it doesn't exist """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        os.chown(path, uid, gid)


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
    with open(dev, 'wb') as f:
        f.seek(-size, os.SEEK_END)
        f.write(size*b'\0')


def enable_yum_priority_obsoletes(path="/etc/yum/pluginconf.d/priorities.conf"):
    """Configure Yum priorities to include obsoletes"""
    config = configparser.ConfigParser()
    config.read(path)
    config.set('main', 'check_obsoletes', '1')
    with open(path, 'w') as fout:
        config.write(fout)


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
