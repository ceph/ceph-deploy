import argparse
import logging

from cStringIO import StringIO

from . import exc
from . import conf
from .cliutil import priority


log = logging.getLogger(__name__)

def admin(args):
    cfg = conf.load(args)
    conf_data = StringIO()
    cfg.write(conf_data)

    errors = 0
    for hostname in args.client:
        log.debug('Pushing config to %s', hostname)
        try:
            sudo = args.pushy('ssh+sudo:{hostname}'.format(
                    hostname=hostname,
                    ))

            write_conf_r = sudo.compile(conf.write_conf)
            write_conf_r(
                cluster=args.cluster,
                conf=conf_data.getvalue(),
                overwrite=args.overwrite_conf,
                )

        except RuntimeError as e:
            log.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to config %d hosts' % errors)


@priority(70)
def make(parser):
    """
    Push configuration file to a remote host.
    """
    parser.add_argument(
        'client',
        metavar='HOST',
        nargs='*',
        help='host to configure',
        )
    parser.set_defaults(
        func=admin,
        )
