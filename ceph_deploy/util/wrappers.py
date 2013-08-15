"""
In a lot of places we need to make system calls, mainly through subprocess.
Here we define them and reuse them with the added functionality of getting
logging and remote execution.

This allows us to only remote-execute the actual calls, not whole functions.
"""
from ceph_deploy.util.decorators import remote_compile
from ceph_deploy.util import context


def check_call(conn, logger, args, *a, **kw):
    """
    Wraps ``subprocess.check_call`` for a remote call via ``pushy``
    doing all the capturing and logging nicely upon failure/success

    The mangling of the traceback when an exception ocurrs, is because the
    caller gets eating up by not being executed in the actual function of
    a given module (e.g. ``centos/install.py``) but rather here, where the
    stack trace is no longer relevant.

    :param args: The args to be passed onto ``check_call``
    """
    command = ' '.join(args)
    patch = kw.pop('patch', True)  # Always patch unless explicitly told to
    logger.info('Running command: %s' % command)

    def remote_call(args, *a, **kw):
        import subprocess
        subprocess.check_call(
            args,
            *a,
            **kw
        )

    with context.remote(conn, logger, remote_call, mangle_exc=False, patch=patch) as call:
        try:
            return call(args, *a, **kw)
        except Exception as err:
            import inspect
            stack = inspect.getframeinfo(inspect.currentframe().f_back)
            if hasattr(err, 'remote_traceback'):
                logger.error('Traceback (most recent call last):')
                logger.error('  File "%s", line %s, in %s' % (
                    stack[0],
                    stack[1],
                    stack[2])
                )
                err.remote_traceback.pop(0)
                for line in err.remote_traceback:
                    if line:
                        logger.error(line)
                raise RuntimeError('Failed to execute command: %s' % ' '.join(args))
            else:
                raise err
