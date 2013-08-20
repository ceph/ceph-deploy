import StringIO
from ceph_deploy.util.decorators import remote_compile


class remote(object):
    """
    Context manager for capturing all stdout, stderr on a remote client by
    monkeypatching pushy's ``sys.stdout`` and ``sys.stderr`` modules when
    executing remotely.

    It will take care of compiling the function passed in so that the only
    action left to the user of this context manager is to call that function
    with whatever arguments are necessary.

    For example::

        with remote(client, logger, my_func) as remote_func:
            remote_func(my_arg, my_other_arg)


    At exit, it will use the logger instance to report errors (from captured
    stderr) or info messages (from stdout).
    """

    def __init__(self, client, logger, func, mangle_exc=True, patch=True):
        self.client = client
        self.logger = logger
        self.func = func
        self.description = getattr(func, 'func_doc')
        self.mangle_exc = mangle_exc
        self.patch = patch

    def __enter__(self):
        if self.patch:
            self.stdout = self.client.modules.sys.stdout
            self.stderr = self.client.modules.sys.stderr

            self.client.modules.sys.stdout = StringIO.StringIO()
            self.client.modules.sys.stderr = StringIO.StringIO()
        if self.description:
            self.logger.info(self.description.strip())
        return remote_compile(self.client, self.func)

    def __exit__(self, e_type, e_val, e_traceback):
        if self.patch:
            stdout_lines = self.client.modules.sys.stdout.getvalue()
            stderr_lines = self.client.modules.sys.stderr.getvalue()
            self.write_log(stdout_lines, 'info')
            self.write_log(stderr_lines, 'error')

            # leave everything as it was
            self.client.modules.sys.stdout = self.stdout
            self.client.modules.sys.stdout = self.stderr

        if not self.mangle_exc:
            return False

        if e_type is not None:
            if hasattr(e_val, 'remote_traceback'):
                for line in e_val.remote_traceback:
                    if line:
                        self.logger.error(line)
                return True  # So that we eat up the traceback

    def write_log(self, lines, log_level):
        logger = getattr(self.logger, log_level)
        for line in lines.split('\n'):
            if line:
                logger(line)
