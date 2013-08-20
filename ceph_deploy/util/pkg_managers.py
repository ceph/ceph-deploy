from ceph_deploy.util import wrappers


def apt(conn, logger, package, *a, **kw):
    cmd = [
        'env',
        'DEBIAN_FRONTEND=noninteractive',
        'apt-get',
        '-q',
        'install',
        '--assume-yes',
        package,
    ]
    return wrappers.check_call(
        conn,
        logger,
        cmd,
        *a,
        **kw
    )


def apt_update(conn, logger):
    cmd = [
        'apt-get',
        '-q',
        'update',
    ]
    return wrappers.check_call(
        conn,
        logger,
        cmd,
    )


def yum(conn, logger, package, *a, **kw):
    cmd = [
        'yum',
        '-y',
        '-q',
        'install',
        package,
    ]
    return wrappers.check_call(
        conn,
        logger,
        cmd,
        *a,
        **kw
    )


def rpm(conn, logger, rpm_args=None, *a, **kw):
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
    return wrappers.check_call(
        conn,
        logger,
        cmd,
        *a,
        **kw
    )
