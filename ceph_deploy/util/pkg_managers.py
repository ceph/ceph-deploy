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
