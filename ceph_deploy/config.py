import logging
import os.path

from ceph_deploy import exc
from ceph_deploy import conf
from ceph_deploy.cliutil import priority
from ceph_deploy import hosts

LOG = logging.getLogger(__name__)


def config_push(args):
    conf_data = conf.ceph.load_raw(args)

    errors = 0
    for hostname in args.client:
        LOG.debug('Pushing config to %s', hostname)
        try:
            distro = hosts.get(hostname, username=args.username)

            distro.conn.remote_module.write_conf(
                args.cluster,
                conf_data,
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
                    with open(topath, 'rb') as f:
                        existing = f.read()
                        if existing != conf_file_contents and not args.overwrite_conf:
                            LOG.error('local config file %s exists with different content; use --overwrite-conf to overwrite' % topath)
                            raise

                with open(topath, 'wb') as f:
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
    Copy ceph.conf to/from remote host(s)
    """
    config_parser = parser.add_subparsers(dest='subcommand')
    config_parser.required = True

    config_push = config_parser.add_parser(
        'push',
        help='push Ceph config file to one or more remote hosts'
        )
    config_push.add_argument(
        'client',
        metavar='HOST',
        nargs='+',
        help='host(s) to push the config file to',
        )

    config_pull = config_parser.add_parser(
        'pull',
        help='pull Ceph config file from one or more remote hosts'
        )
    config_pull.add_argument(
        'client',
        metavar='HOST',
        nargs='+',
        help='host(s) to pull the config file from',
        )
    parser.set_defaults(
        func=config,
        )
