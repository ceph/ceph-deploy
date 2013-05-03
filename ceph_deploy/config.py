import logging

from cStringIO import StringIO

from . import exc
from . import conf
from . import misc
from .cliutil import priority
from .sudo_pushy import get_transport

LOG = logging.getLogger(__name__)

def config_push(args):
    cfg = conf.load(args)
    conf_data = StringIO()
    cfg.write(conf_data)

    errors = 0
    for hostname in args.client:
        LOG.debug('Pushing config to %s', hostname)
        try:
            sudo = args.pushy(get_transport(hostname))
            write_conf_r = sudo.compile(conf.write_conf)
            write_conf_r(
                cluster=args.cluster,
                conf=conf_data.getvalue(),
                overwrite=args.overwrite_conf,
                )
            sudo.close()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to config %d hosts' % errors)


def config_pull(args):
    import os.path

    topath = '{cluster}.conf'.format(cluster=args.cluster)
    frompath = '/etc/ceph/{cluster}.conf'.format(cluster=args.cluster)

    errors = 0
    for hostname in args.client:
        try:
            LOG.debug('Checking %s for %s', hostname, frompath)
            sudo = args.pushy(get_transport(hostname))
            get_file_r = sudo.compile(misc.get_file)
            conf_file = get_file_r(path=frompath)
            if conf_file is not None:
                LOG.debug('Got %s from %s', frompath, hostname)
                if os.path.exists(topath):
                    with file(topath, 'rb') as f:
                        existing = f.read()
                        if existing != conf_file and not args.overwrite_conf:
                            LOG.error('local config file %s exists with different content; use --overwrite-conf to overwrite' % topath)
                            raise

                with file(topath, 'w') as f:
                    f.write(conf_file)
                return
            sudo.close()
            LOG.debug('Empty or missing %s on %s', frompath, hostname)
        except:
            LOG.error('Unable to pull %s from %s', frompath, hostname)
        finally:
            errors += 1

    raise exc.GenericError('Failed to fetch config from %d hosts' % errors)


def config(args):
    if args.subcommand == 'push':
        config_push(args)
    elif args.subcommand == 'pull':
        config_pull(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)

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
