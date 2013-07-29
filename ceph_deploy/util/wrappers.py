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

    :param args: The args to be passed onto ``check_call``
    """
    command = ' '.join(args)
    logger.info('Running command: %s' % command)

    def remote_call(args, *a, **kw):
        import subprocess
        subprocess.check_call(
            args,
            *a,
            **kw
        )

    with context.remote(conn, logger, remote_call) as call:
        return call(args, *a, **kw)
