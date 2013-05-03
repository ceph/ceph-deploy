import logging

from cStringIO import StringIO

from . import exc
from . import conf
from .cliutil import priority
from .sudo_pushy import get_transport

LOG = logging.getLogger(__name__)

def write_file(path, content):
    try:
        with file(path, 'w') as f:
            f.write(content)
    except:
        pass        

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
            sudo = args.pushy(get_transport(hostname))
            write_conf_r = sudo.compile(conf.write_conf)
            write_conf_r(
                cluster=args.cluster,
                conf=conf_data.getvalue(),
                overwrite=args.overwrite_conf,
                )

            sudo = args.pushy(get_transport(hostname))
            write_file_r = sudo.compile(write_file)
            error = write_file_r(
                '/etc/ceph/%s.client.admin.keyring' % args.cluster,
                keyring
                )
            if error is not None:
                raise exc.GenericError(error)
            sudo.close()

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
