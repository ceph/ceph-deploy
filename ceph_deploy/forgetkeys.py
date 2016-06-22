import logging
import errno

from .cliutil import priority


LOG = logging.getLogger(__name__)


def forgetkeys(args):
    import os
    for f in [
        'mon',
        'client.admin',
        'bootstrap-osd',
        'bootstrap-mds',
        'bootstrap-rgw',
        ]:
        try:
            os.unlink('{cluster}.{what}.keyring'.format(
                    cluster=args.cluster,
                    what=f,
                    ))
        except OSError as e:
            if e.errno == errno.ENOENT:
                pass
            else:
                raise

@priority(100)
def make(parser):
    """
    Remove authentication keys from the local directory.
    """
    parser.set_defaults(
        func=forgetkeys,
        )
