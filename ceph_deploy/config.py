import logging
from cStringIO import StringIO
import os.path

from . import exc
from . import conf
from .cliutil import priority
from . import hosts

LOG = logging.getLogger(__name__)


def config_push(args):
    cfg = conf.load(args)
    conf_data = StringIO()
    cfg.write(conf_data)

    errors = 0
    for hostname in args.client:
        LOG.debug('Pushing config to %s', hostname)
        try:
            distro = hosts.get(hostname, username=args.username)

            distro.conn.remote_module.write_conf(
                args.cluster,
                conf_data.getvalue(),
                args.overwrite_conf,
            )

            distro.conn.exit()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to config %d hosts' % errors)


def config_pull(args):

    topath = '{cluster}.conf'.format(cluster=args.cluster)
    frompath = '/etc/ceph/{cluster}.conf'.format(cluster=args.cluster)

    errors = 0
    for hostname in args.client:
        try:
            LOG.debug('Checking %s for %s', hostname, frompath)
            distro = hosts.get(hostname, username=args.username)
            conf_file_contents = distro.conn.remote_module.get_file(frompath)

            if conf_file_contents is not None:
                LOG.debug('Got %s from %s', frompath, hostname)
                if os.path.exists(topath):
                    with file(topath, 'rb') as f:
                        existing = f.read()
                        if existing != conf_file_contents and not args.overwrite_conf:
                            LOG.error('local config file %s exists with different content; use --overwrite-conf to overwrite' % topath)
                            raise

                with file(topath, 'w') as f:
                    f.write(conf_file_contents)
                return
            distro.conn.exit()
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
