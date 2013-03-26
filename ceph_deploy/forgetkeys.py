import logging

from . import misc
from .cliutil import priority


LOG = None


def forgetkeys(args):
    import os

    global LOG
    LOG = misc.get_logger(args)

    LOG.info('Forgetting local keys...')

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
