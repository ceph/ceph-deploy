import logging

from .cliutil import priority


LOG = logging.getLogger(__name__)


def forgetkeys(args):
    import os
    for f in [
        'mon',
        'client.admin',
        'bootstrap-osd',
        'bootstrap-mds',
        ]:
        os.unlink('{cluster}.{what}.keyring'.format(
                cluster=args.cluster,
                what=f,
                ))

@priority(100)
def make(parser):
    """
    Remove authentication keys from the local directory.
    """
    parser.set_defaults(
        func=forgetkeys,
        )
