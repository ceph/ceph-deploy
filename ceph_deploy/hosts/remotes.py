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
    tmp_file = tempfile.NamedTemporaryFile()
    err_msg = 'config file %s exists with different content; use --overwrite-conf to overwrite' % path

    if os.path.exists(path):
        with file(path, 'rb') as f:
            old = f.read()
            if old != conf and not overwrite:
                raise RuntimeError(err_msg)
    tmp_file.write(conf)
    os.rename(tmp_file.name, path)


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
