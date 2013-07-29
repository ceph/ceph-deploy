import StringIO


class capsys(object):
    """
    Context manager for capturing all stdout, stderr on a remote client by
    monkeypatching pushy's ``sys.stdout`` and ``sys.stderr`` modules when
    executing remotely.

    At exit, it will use the logger instance to report errors (from captured
    stderr) or info messages (from stdout).
    """

    def __init__(self, client, logger):
        self.client = client
        self.logger = logger

    def __enter__(self):
        self.stdout = self.client.modules.sys.stdout
        self.stderr = self.client.modules.sys.stderr

        self.client.modules.sys.stdout = StringIO.StringIO()
        self.client.modules.sys.stderr = StringIO.StringIO()

    def __exit__(self, *args, **kwargs):
        stdout_lines = self.client.modules.sys.stdout.getvalue()
        stderr_lines = self.client.modules.sys.stderr.getvalue()
        self.write_log(stdout_lines, 'info')
        self.write_log(stderr_lines, 'error')

        # leave everything as it was
        self.client.modules.sys.stdout = self.stdout
        self.client.modules.sys.stdout = self.stderr

    def write_log(self, lines, log_level):
        logger = getattr(self.logger, log_level)
        for line in lines.split('\n'):
            if line:
                logger(line)
