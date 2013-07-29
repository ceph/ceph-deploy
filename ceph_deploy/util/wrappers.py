"""
In a lot of places we need to make system calls, mainly through subprocess.
Here we define them and reuse them with the added functionality of getting
logging and remote execution.

This allows us to only remote-execute the actual calls, not whole functions.
"""
from ceph_deploy.util.decorators import remote_compile
from ceph_deploy.util import context


def check_call(args, logger, conn, *a, **kw):
    command = ' '.join(args)
    logger.info('Running command: %s' % command)

    def remote_call(args, *a, **kw):
        import subprocess
        subprocess.check_call(
            args,
            *a,
            **kw
        )

    compile_ = remote_compile(conn, remote_call)
    with context.capsys(conn, logger):
        try:
            return compile_(args, *a, **kw)
        except Exception as err:
            if getattr(err, 'remote_traceback'):
                for line in err.remote_traceback:
                    logger.error(line)
            else:
                raise


def generic_remote(func, logger, conn, *a, **kw):
    """
    This generic remote wrapper will introspect the docstring from ``func`` to
    log out the action about to be done. It better be succinct.
    """
    action = getattr(func, 'func_doc', func.func_name)
    logger.info('Executing action: %s' % action)

    compile_ = remote_compile(conn, func)
    with context.capsys(conn, logger):
        try:
            return compile_(*a, **kw)
        except Exception as err:
            if getattr(err, 'remote_traceback'):
                for line in err.remote_traceback:
                    logger.error(line)
            else:
                raise
