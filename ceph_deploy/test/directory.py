import contextlib
import os


@contextlib.contextmanager
def directory(path):
    prev = os.open('.', os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.chdir(path)
        yield
    finally:
        os.fchdir(prev)
        os.close(prev)
