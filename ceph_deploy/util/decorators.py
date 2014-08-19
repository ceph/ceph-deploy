import logging
import sys
import traceback
from functools import wraps


def catches(catch=None, handler=None, exit=True, handle_all=False):
    """
    Very simple decorator that tries any of the exception(s) passed in as
    a single exception class or tuple (containing multiple ones) returning the
    exception message and optionally handling the problem if it raises with the
    handler if it is provided.

    So instead of doing something like this::

        def bar():
            try:
                some_call()
                print "Success!"
            except TypeError, exc:
                print "Error while handling some call: %s" % exc
                sys.exit(1)

    You would need to decorate it like this to have the same effect::

        @catches(TypeError)
        def bar():
            some_call()
            print "Success!"

    If multiple exceptions need to be caught they need to be provided as a
    tuple::

        @catches((TypeError, AttributeError))
        def bar():
            some_call()
            print "Success!"

    If adding a handler, it should accept a single argument, which would be the
    exception that was raised, it would look like::

        def my_handler(exc):
            print 'Handling exception %s' % str(exc)
            raise SystemExit

        @catches(KeyboardInterrupt, handler=my_handler)
        def bar():
            some_call()

    Note that the handler needs to raise its SystemExit if it wants to halt
    execution, otherwise the decorator would continue as a normal try/except
    block.


    :param catch: A tuple with one (or more) Exceptions to catch
    :param handler: Optional handler to have custom handling of exceptions
    :param exit: Raise a ``SystemExit`` after handling exceptions
    :param handle_all: Handle all other exceptions via logging.
    """
    catch = catch or Exception
    logger = logging.getLogger('ceph_deploy')

    def decorate(f):

        @wraps(f)
        def newfunc(*a, **kw):
            exit_from_catch = False
            try:
                return f(*a, **kw)
            except catch as e:
                if handler:
                    return handler(e)
                else:
                    logger.error(make_exception_message(e))

                    if exit:
                        exit_from_catch = True
                        sys.exit(1)
            except Exception:  # anything else, no need to save the exception as a variable
                if handle_all is False:  # re-raise if we are not supposed to handle everything
                    raise
                # Make sure we don't spit double tracebacks if we are raising
                # SystemExit from the `except catch` block

                if exit_from_catch:
                    sys.exit(1)

                str_failure = traceback.format_exc()
                for line in str_failure.split('\n'):
                    logger.error("%s" % line)
                sys.exit(1)

        return newfunc

    return decorate

#
# Decorator helpers
#


def make_exception_message(exc):
    """
    An exception is passed in and this function
    returns the proper string depending on the result
    so it is readable enough.
    """
    if str(exc):
        return '%s: %s\n' % (exc.__class__.__name__, exc)
    else:
        return '%s\n' % (exc.__class__.__name__)

