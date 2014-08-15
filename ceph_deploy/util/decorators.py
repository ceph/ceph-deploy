import logging
import os
import sys
import traceback
from functools import wraps


def catches(catch=None, handler=None, exit=True):
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
            except Exception as err:  # anything else
                # Make sure we don't spit double tracebacks if we are raising
                # SystemExit from the `except catch` block
                if exit_from_catch:
                    sys.exit(1)

                str_failure = traceback.format_exc(err)
                if str_failure:
                    for line in str_failure.split('\n'):
                        logger.error("%s" % line)
                else:  # if for whatever reason we can't get an err message
                    logger.error(make_exception_message(err))

            finally:
                # This block is crucial to avoid having issues with
                # Python spitting non-sense thread exceptions. We have already
                # handled what we could, so close stderr and stdout.
                if not os.environ.get('CEPH_DEPLOY_TEST'):
                    import sys
                    try:
                        sys.stdout.close()
                    except:
                        pass
                    try:
                        sys.stderr.close()
                    except:
                        pass

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

