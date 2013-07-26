

def remote_compile(client, fn, logger):
    def outer(fn):
        from functools import wraps
        @wraps(fn)
        def inner(*args, **kwargs):
            class RemoteException(Exception):

                def __init__(self, remote_traceback):
                    self.remote_traceback = remote_traceback

            try:
                fn(*args, **kwargs)
            except:
                import traceback
                remote_trace = traceback.format_exc()
                raise RemoteException(remote_trace.split('\n'))
        return inner
    return client.compile(outer)(client.compile(fn))
