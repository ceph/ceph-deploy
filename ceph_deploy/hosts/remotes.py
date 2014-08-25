import ConfigParser
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


def write_sources_list(url, codename, filename='ceph.list'):
    """add deb repo to sources.list"""
    repo_path = os.path.join('/etc/apt/sources.list.d', filename)
    with file(repo_path, 'w') as f:
        f.write('deb {url} {codename} main\n'.format(
                url=url,
                codename=codename,
                ))


def write_yum_repo(content, filename='ceph.repo'):
    """set the contents of repo file to /etc/yum.repos.d/"""
    repo_path = os.path.join('/etc/yum.repos.d', filename)
    write_file(repo_path, content)


def set_repo_priority(sections, path='/etc/yum.repos.d/ceph.repo', priority='1'):
    Config = ConfigParser.ConfigParser()
    Config.read(path)
    Config.sections()
    for section in sections:
        try:
            Config.set(section, 'priority', priority)
        except ConfigParser.NoSectionError:
            # Emperor versions of Ceph used all lowercase sections
            # so lets just try again for the section that failed, maybe
            # we are able to find it if it is lower
            Config.set(section.lower(), 'priority', priority)

    with open(path, 'wb') as fout:
        Config.write(fout)

    # And now, because ConfigParser is super duper, we need to remove the
    # assignments so this looks like it was before
    def remove_whitespace_from_assignments():
        separator = "="
        lines = file(path).readlines()
        fp = open(path, "w")
        for line in lines:
            line = line.strip()
            if not line.startswith("#") and separator in line:
                assignment = line.split(separator, 1)
                assignment = map(str.strip, assignment)
                fp.write("%s%s%s\n" % (assignment[0], separator, assignment[1]))
            else:
                fp.write(line + "\n")

    remove_whitespace_from_assignments()


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
        os.chmod(path, 0644)
        return
    if os.path.exists('/etc/ceph'):
        with open(path, 'w') as f:
            f.write(conf)
        os.chmod(path, 0644)
    else:
        err_msg = '/etc/ceph/ does not exist - could not write config'
        raise RuntimeError(err_msg)


def write_keyring(path, key):
    """ create a keyring file """
    # Note that we *require* to avoid deletion of the temp file
    # otherwise we risk not being able to copy the contents from
    # one file system to the other, hence the `delete=False`
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(key)
    tmp_file.close()
    keyring_dir = os.path.dirname(path)
    if not path_exists(keyring_dir):
        makedir(keyring_dir)
    shutil.move(tmp_file.name, path)


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


def readline(path):
    with open(path) as _file:
        return _file.readline().strip('\n')


def path_exists(path):
    return os.path.exists(path)


def get_realpath(path):
    return os.path.realpath(path)


def listdir(path):
    return os.listdir(path)


def makedir(path, ignored=None):
    ignored = ignored or []
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno in ignored:
            pass
        else:
            # re-raise the original exception
            raise


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
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
    shutil.move(path, os.path.join('/var/lib/ceph/mon-removed/', file_name))


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
