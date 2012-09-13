import ConfigParser
import logging
import re

from cStringIO import StringIO

from . import conf
from . import exc
from .memoize import memoize


log = logging.getLogger(__name__)


def get_bootstrap_osd_key(cluster):
    """
    Run on mon node, extract bootstrap-osd key for `cluster`.
    """
    path = '/var/lib/ceph/bootstrap-osd/{cluster}.keyring'.format(cluster=cluster)
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        pass


def find_bootstrap_osd_key(args, cfg):
    """
    Look at all the mon nodes, see if they have a bootstrap-osd key.

    Returns key as string, or None.
    """
    log.debug('Looking for mon to grab bootstrap key from...')
    try:
        mon_host = cfg.get('global', 'mon_host')
    except (ConfigParser.NoSectionError,
            ConfigParser.NoOptionError):
        mon_host = ''

    mons = re.split(r'[,\s]+', mon_host)
    if not mons:
        raise exc.NeedMonError()

    for hostname in mons:
        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(hostname=hostname))
        get_bootstrap_osd_key_r = sudo.compile(get_bootstrap_osd_key)
        key = get_bootstrap_osd_key_r(
            cluster=args.cluster,
            )
        if key is not None:
            log.debug('Got bootstrap key from %s.', hostname)
            return key


def write_conf(cluster, conf):
    import os

    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp = '{path}.{pid}.tmp'.format(path=path, pid=os.getpid())

    with file(tmp, 'w') as f:
        f.write(conf)
        f.flush()
        os.fsync(f)
    os.rename(tmp, path)


def create_osd(cluster, find_key):
    """
    Run on osd node, writes the bootstrap key if not there yet.

    Returns None on success, error message on error exceptions. pushy
    mangles exceptions to all be of type ExceptionProxy, so we can't
    tell between bug and correctly handled failure, so avoid using
    exceptions for non-exceptional runs.
    """
    import os
    import subprocess

    path = '/var/lib/ceph/bootstrap-osd/{cluster}.keyring'.format(
        cluster=cluster,
        )
    if not os.path.exists(path):
        key = find_key()
        if key is None:
            return 'bootstrap-osd key not found, mons are not ready.'
        tmp = '{path}.{pid}.tmp'.format(
            path=path,
            pid=os.getpid(),
            )
        # file() doesn't let us control access mode from the
        # beginning, and thus would have a race where attacker can
        # open before we chmod the file, so play games with os.open
        fd = os.open(
            tmp,
            (os.O_WRONLY|os.O_CREAT|os.O_EXCL
             |os.O_NOCTTY|os.O_NOFOLLOW),
            0600,
            )
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
            f.flush()
            os.fsync(f)
        os.rename(tmp, path)

    # in case disks have been prepared before we do this, activate
    # them now
    subprocess.check_call(
        args=[
            'udevadm',
            'trigger',
            '--subsystem-match=block',
            '--action=add',
            ],
        )


def osd(args):
    cfg = conf.load(args)

    log.debug(
        'Deploying osd, cluster %s hosts %s',
        args.cluster,
        ' '.join(args.osd),
        )

    @memoize
    def find_key():
        """
        Wrapper function to pass config and avoid redoing work.
        """
        return find_bootstrap_osd_key(
            args=args,
            cfg=cfg,
            )

    for hostname in args.osd:
        log.debug('Deploying osd to %s', hostname)

        # TODO username
        sudo = args.pushy('ssh+sudo:{hostname}'.format(
                hostname=hostname,
                ))

        write_conf_r = sudo.compile(write_conf)
        conf_data = StringIO()
        cfg.write(conf_data)
        write_conf_r(
            cluster=args.cluster,
            conf=conf_data.getvalue(),
            )

        create_osd_r = sudo.compile(create_osd)
        error = create_osd_r(
            cluster=args.cluster,
            find_key=find_key,
            )
        if error is not None:
            raise exc.GenericError(error)
        log.debug('Host %s is now ready for osd use.', hostname)


def make(parser):
    """
    Deploy ceph osd on remote hosts.
    """
    parser.add_argument(
        'osd',
        metavar='HOST',
        nargs='+',
        help='host to deploy on',
        )
    parser.set_defaults(
        func=osd,
        )
