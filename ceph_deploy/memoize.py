import functools


class NotFound(object):
    """
    Sentinel object to say call was not memoized.

    Supposed to be faster than throwing exceptions on cache miss.
    """
    def __str__(self):
        return self.__class__.__name__

NotFound = NotFound()


def memoize(f):
    cache = {}

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.iteritems())))
        val = cache.get(key, NotFound)
        if val is NotFound:
            val = cache[key] = f(*args, **kwargs)
        return val
    return wrapper
