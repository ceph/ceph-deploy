import os
import subprocess
import sys


def _prepend_path(env):
    """
    Make sure the PATH contains the location where the Python binary
    lives. This makes sure cli tools installed in a virtualenv work.
    """
    if env is None:
        env = os.environ
    env = dict(env)
    new = os.path.dirname(sys.executable)
    path = env.get('PATH')
    if path is not None:
        new = new + ':' + path
    env['PATH'] = new
    return env


class CLIProcess(object):
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        try:
            self.p = subprocess.Popen(**self.kw)
        except OSError as e:
            raise AssertionError(
                'CLI tool {args!r} does not work: {err}'.format(
                    args=self.kw['args'],
                    err=e,
                    ),
                )
        else:
            return self.p

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.p.wait()
        if self.p.returncode != 0:
            raise AssertionError(
                'CLI tool {args!r} failed: {status}'.format(
                    args=self.kw['args'],
                    status=self.p.returncode,
                    ),
                )


class CLITester(object):
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def __call__(self, **kw):
        kw.setdefault('cwd', str(self.tmpdir))
        kw['env'] = _prepend_path(kw.get('env'))
        return CLIProcess(**kw)


def pytest_funcarg__cli(request):
    """
    Test command line behavior.
    """

    # the tmpdir here will be the same value as the test function
    # sees; we rely on that to let caller prepare and introspect
    # any files the cli tool will read or create
    tmpdir = request.getfuncargvalue('tmpdir')

    return CLITester(tmpdir=tmpdir)
