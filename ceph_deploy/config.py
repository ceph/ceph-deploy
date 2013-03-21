import argparse
import logging

from cStringIO import StringIO

from . import exc
from . import conf
from .cliutil import priority
from . import misc

log = logging.getLogger(__name__)

def config_push(args):
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


def get_file(path):
    """
    Run on mon node, grab a file.
    """
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        pass

def config_pull(args):
    topath = '{cluster}.conf'.format(cluster=args.cluster)
    frompath = '/etc/ceph/{cluster}.conf'.format(cluster=args.cluster)

    errors = 0
    for hostname in args.client:
        try:
            log.debug('Checking %s for %s', hostname, frompath)
            sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
            get_file_r = sudo.compile(get_file)
            conf = get_file_r(path=frompath)
            if conf is not None:
                log.debug('Got %s from %s', frompath, hostname)
                if os.path.exists(topath):
                    with file(topath, 'rb') as f:
                        existing = f.read()
                        if existing != conf and not args.overwrite_conf:
                            log.error('local config file %s exists with different content; use --overwrite-conf to overwrite' % topath)
                            raise

                with file(topath, 'w') as f:
                    f.write(conf)
                return
            log.debug('Empty or missing %s on %s', frompath, hostname)
        except:
            log.error('Unable to pull %s from %s', frompath, hostname)
        finally:
            errors += 1

    raise exc.GenericError('Failed to fetch config from %d hosts' % errors)


def config(args):
    if args.subcommand == 'push':
        config_push(args)
    elif args.subcommand == 'pull':
        config_pull(args)
    else:
        log.error('subcommand %s not implemented', args.subcommand)

@priority(70)
def make(parser):
    """
    Push configuration file to a remote host.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'push',
            'pull',
            ],
        help='push or pull',
        )
    parser.add_argument(
        'client',
        metavar='HOST',
        nargs='*',
        help='host to push/pull the config to/from',
        )
    parser.set_defaults(
        func=config,
        )
