from ceph_deploy.lib import remoto


def apt(conn, packages, *a, **kw):
    if isinstance(packages, str):
        packages = [packages]
    cmd = [
        'env',
        'DEBIAN_FRONTEND=noninteractive',
        'apt-get',
        'install',
        '--assume-yes',
    ]
    cmd.extend(packages)
    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def apt_remove(conn, packages, *a, **kw):
    if isinstance(packages, str):
        packages = [packages]

    purge = kw.pop('purge', False)
    cmd = [
        'apt-get',
        '-q',
        'remove',
        '-f',
        '-y',
        '--force-yes',
    ]
    if purge:
        cmd.append('--purge')
    cmd.extend(packages)

    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def apt_update(conn):
    cmd = [
        'apt-get',
        '-q',
        'update',
    ]
    return remoto.process.run(
        conn,
        cmd,
    )


def yum(conn, packages, *a, **kw):
    if isinstance(packages, str):
        packages = [packages]

    cmd = [
        'yum',
        '-y',
        'install',
    ]
    cmd.extend(packages)
    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def yum_remove(conn, packages, *a, **kw):
    cmd = [
        'yum',
        '-y',
        '-q',
        'remove',
    ]
    if isinstance(packages, str):
        cmd.append(packages)
    else:
        cmd.extend(packages)
    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def yum_clean(conn, item=None):
    item = item or 'all'
    cmd = [
        'yum',
        'clean',
        item,
    ]

    return remoto.process.run(
        conn,
        cmd,
    )


def rpm(conn, rpm_args=None, *a, **kw):
    """
    A minimal front end for ``rpm`. Extra flags can be passed in via
    ``rpm_args`` as an iterable.
    """
    rpm_args = rpm_args or []
    cmd = [
        'rpm',
        '-Uvh',
    ]
    cmd.extend(rpm_args)
    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def zypper(conn, packages, *a, **kw):
    if isinstance(packages, str):
        packages = [packages]

    cmd = [
        'zypper',
        '--non-interactive',
        'install',
    ]

    cmd.extend(packages)
    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def zypper_remove(conn, packages, *a, **kw):
    cmd = [
        'zypper',
        '--non-interactive',
        '--quiet',
        'remove',
        ]

    if isinstance(packages, str):
        cmd.append(packages)
    else:
        cmd.extend(packages)
    return remoto.process.run(
        conn,
        cmd,
        *a,
        **kw
    )


def zypper_refresh(conn):
    cmd = [
        'zypper',
        '--non-interactive',
        'refresh',
        ]

    return remoto.process.run(
        conn,
        cmd
    )


class PackageManager(object):
    """
    Base class for all Package Managers
    """

    def __init__(self, remote_conn):
        self.remote_info = remote_conn
        self.remote_conn = remote_conn.conn

    def _run(self, cmd):
        return remoto.process.run(
            self.remote_conn,
            cmd
        )

    def install(self, packages):
        """Install packages on remote node"""
        raise NotImplementedError()

    def remove(self, packages):
        """Uninstall packages on remote node"""
        raise NotImplementedError()

    def clean(self):
        """Clean metadata/cache"""
        raise NotImplementedError()


class RPMManagerBase(PackageManager):
    """
    Base class to hold common pieces of Yum and DNF
    """

    executable = None

    def install(self, packages):
        if isinstance(packages, str):
            packages = [packages]

        cmd = [
            self.executable,
            '-y',
            'install',
        ]
        cmd.extend(packages)
        return self._run(cmd)

    def remove(self, packages):
        if isinstance(packages, str):
            packages = [packages]

        cmd = [
            self.executable,
            '-y',
            '-q',
            'remove',
        ]
        cmd.extend(packages)
        return self._run(cmd)

    def clean(self, item=None):
        item = item or 'all'
        cmd = [
            self.executable,
            'clean',
            item,
        ]

        return self._run(cmd)


class DNF(RPMManagerBase):
    """
    The DNF Package manager
    """

    executable = 'dnf'

    def install_priorities_plugin(self):
        # DNF supports priorities natively
        pass


class Yum(RPMManagerBase):
    """
    The Yum Package manager
    """

    executable = 'yum'

    def install_priorities_plugin(self):
        package_name = 'yum-plugin-priorities'

        if self.remote_info.normalized_name == 'centos':
            if self.remote_info.normalized_release.int_major != 6:
                package_name = 'yum-priorities'
        self.install(package_name)
