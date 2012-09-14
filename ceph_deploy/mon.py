import ConfigParser
import logging
import re

from cStringIO import StringIO

from . import conf
from . import exc


log = logging.getLogger(__name__)


def write_conf(cluster, conf):
    import os

    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp = '{path}.{pid}.tmp'.format(path=path, pid=os.getpid())

    with file(tmp, 'w') as f:
        f.write(conf)
        f.flush()
        os.fsync(f)
    os.rename(tmp, path)


def create_mon(cluster, get_monitor_secret):
    import os
    import socket
    import subprocess

    hostname = socket.gethostname()
    done_path = '/var/lib/ceph/mon/ceph-{hostname}/done'.format(
        hostname=hostname,
        )

    if not os.path.exists(done_path):
        keyring = '/var/lib/ceph/tmp/{cluster}-{hostname}.mon.keyring'.format(
            cluster=cluster,
            hostname=hostname,
            )
        monitor_secret = get_monitor_secret()

        # TODO don't put the key in "ps" output, stdout
        subprocess.check_call(
            args=[
                'ceph-authtool',
                keyring,
                '--create-keyring',
                '--name=mon.',
                '--add-key={monitor_secret}'.format(
                    monitor_secret=monitor_secret,
                    ),
                '--cap', 'mon', 'allow *',
                ],
            )

        subprocess.check_call(
            args=[
                'ceph-mon',
                '--cluster', cluster,
                '--mkfs',
                '-i', hostname,
                '--keyring', keyring,
                ],
            )
        os.unlink(keyring)
        with file(done_path, 'w'):
            pass

    subprocess.check_call(
        args=[
            'initctl',
            'emit',
            'ceph-mon',
            'cluster={cluster}'.format(cluster=cluster),
            'id={hostname}'.format(hostname=hostname),
            ],
        )


def mon(args):
    cfg = conf.load(args)
    if not args.mon:
        try:
            mon_initial_members = cfg.get('global', 'mon_initial_members')
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            pass
        else:
            args.mon = re.split(r'[,\s]+', mon_initial_members)

    if not args.mon:
        raise exc.NeedHostError()

    log.debug(
        'Deploying mon, cluster %s hosts %s',
        args.cluster,
        ' '.join(args.mon),
        )

    for hostname in args.mon:
        log.debug('Deploying mon to %s', hostname)

        def get_monitor_secret():
            # TODO look for existing mons
            # TODO create random key
            return 'AQBWDj5QAP6LHhAAskVBnUkYHJ7eYREmKo5qKA=='

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))

        write_conf_r = sudo.compile(write_conf)
        conf_data = StringIO()
        cfg.write(conf_data)
        write_conf_r(
            cluster=args.cluster,
            conf=conf_data.getvalue(),
            )

        create_mon_r = sudo.compile(create_mon)
        create_mon_r(
            cluster=args.cluster,
            get_monitor_secret=get_monitor_secret,
            )

        # TODO add_bootstrap_peer_hint


def make(parser):
    """
    Deploy ceph monitor on remote hosts.
    """
    parser.add_argument(
        'mon',
        metavar='HOST',
        nargs='*',
        help='host to deploy on',
        )
    parser.set_defaults(
        func=mon,
        )
