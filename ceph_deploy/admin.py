import logging

from cStringIO import StringIO

from . import exc
from . import conf
from .cliutil import priority
from . import hosts

LOG = logging.getLogger(__name__)


def admin(args):
    cfg = conf.load(args)
    conf_data = StringIO()
    cfg.write(conf_data)

    try:
        with file('%s.client.admin.keyring' % args.cluster, 'rb') as f:
            keyring = f.read()
    except:
        raise RuntimeError('%s.client.admin.keyring not found' %
                           args.cluster)

    errors = 0
    for hostname in args.client:
        LOG.debug('Pushing admin keys and conf to %s', hostname)
        try:
            distro = hosts.get(hostname)
            hostname = distro.conn.remote_module.shortname()

            distro.conn.remote_module.write_conf(
                args.cluster,
                conf_data.getvalue(),
                args.overwrite_conf,
            )

            distro.conn.remote_module.write_file(
                '/etc/ceph/%s.client.admin.keyring' % args.cluster,
                keyring
            )

            distro.conn.exit()

        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to configure %d admin hosts' % errors)


@priority(70)
def make(parser):
    """
    Push configuration and client.admin key to a remote host.
    """
    parser.add_argument(
        'client',
        metavar='HOST',
        nargs='*',
        help='host to configure for ceph administration',
        )
    parser.set_defaults(
        func=admin,
        )
