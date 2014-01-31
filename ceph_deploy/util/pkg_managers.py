from ceph_deploy.lib.remoto import process


def apt(conn, packages, *a, **kw):
    if isinstance(packages, str):
        packages = [packages]
    cmd = [
        'env',
        'DEBIAN_FRONTEND=noninteractive',
        'apt-get',
        '-q',
        'install',
        '--assume-yes',
    ]
    cmd.extend(packages)
    return process.run(
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
    cmd.append('--')
    cmd.extend(packages)

    return process.run(
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
    return process.run(
        conn,
        cmd,
    )


def yum(conn, packages, *a, **kw):
    if isinstance(packages, str):
        packages = [packages]

    cmd = [
        'yum',
        '-y',
        '-q',
        'install',
    ]
    cmd.extend(packages)
    return process.run(
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
    return process.run(
        conn,
        cmd,
        *a,
        **kw
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
    return process.run(
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
        '--quiet',
        'install',
    ]

    cmd.extend(packages)
    return process.run(
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
    return process.run(
        conn,
        cmd,
        *a,
        **kw
    )
