import argparse
import logging
import os
import sys

from cStringIO import StringIO

from . import conf
from . import exc
from . import lsb, hosts
from .cliutil import priority
from .sudo_pushy import get_transport
from .util.wrappers import check_call


LOG = logging.getLogger(__name__)


def get_bootstrap_osd_key(cluster):
    """
    Read the bootstrap-osd key for `cluster`.
    """
    path = '{cluster}.bootstrap-osd.keyring'.format(cluster=cluster)
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        raise RuntimeError('bootstrap-osd keyring not found; run \'gatherkeys\'')


def create_osd(cluster, key):
    """
    Run on osd node, writes the bootstrap key if not there yet.

    Returns None on success, error message on error exceptions. pushy
    mangles exceptions to all be of type ExceptionProxy, so we can't
    tell between bug and correctly handled failure, so avoid using
    exceptions for non-exceptional runs.
    """
    path = '/var/lib/ceph/bootstrap-osd/{cluster}.keyring'.format(
        cluster=cluster,
        )
    if not os.path.exists(path):
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

    def subproc_call(*args, **kwargs):
        """
        call subproc that might fail, collect returncode and stderr/stdout
        to be used in pushy.compile()d functions.  Returns 4-tuple of
        (process exit code, command, stdout contents, stderr contents)
        """
        import subprocess
        import tempfile

        otmp = tempfile.TemporaryFile()
        etmp = tempfile.TemporaryFile()
        cmd = ' '.join(kwargs['args'])
        ret = 0
        errtxt = ''
        kwargs.update(dict(stdout=otmp, stderr=etmp))
        try:
            subprocess.check_call(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            ret = e.returncode
        except Exception as e:
            ret = -1
            # OSError has errno
            if hasattr(e, 'errno'):
                ret = e.errno
            errtxt = str(e)
        otmp.seek(0)
        etmp.seek(0)
        return (ret, cmd, otmp.read(), errtxt + etmp.read())

    # in case disks have been prepared before we do this, activate
    # them now.
    return subproc_call(
        args=[
            'udevadm',
            'trigger',
            '--subsystem-match=block',
            '--action=add',
            ],
        )


def prepare_disk(cluster, disk, journal, activate_prepared_disk, zap, dmcrypt, dmcrypt_dir):
    """
    Run on osd node, prepares a data disk for use.
    """
    args = [
        'ceph-disk-prepare',
        ]
    if zap:
        args.append('--zap-disk')
    if dmcrypt:
        args.append('--dmcrypt')
        if dmcrypt_dir is not None:
            args.append('--dmcrypt-key-dir')
            args.append(dmcrypt_dir)
    args.extend([
        '--cluster',
        cluster,
        '--',
        disk,
    ])
    if journal is not None:
        args.append(journal)

    def subproc_call(*args, **kwargs):
        """
        call subproc that might fail, collect returncode and stderr/stdout
        to be used in pushy.compile()d functions.  Returns 4-tuple of
        (process exit code, command, stdout contents, stderr contents)
        """
        import subprocess
        import tempfile

        otmp = tempfile.TemporaryFile()
        etmp = tempfile.TemporaryFile()
        cmd = ' '.join(kwargs['args'])
        ret = 0
        errtxt = ''
        kwargs.update(dict(stdout=otmp, stderr=etmp))
        try:
            subprocess.check_call(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            ret = e.returncode
        except Exception as e:
            ret = -1
            # OSError has errno
            if hasattr(e, 'errno'):
                ret = e.errno
            errtxt = str(e)
        otmp.seek(0)
        etmp.seek(0)
        return (ret, cmd, otmp.read(), errtxt + etmp.read())

    ret = subproc_call(args=args)
    if ret[0]:
        return ret
    if activate_prepared_disk:
        ret = subproc_call(
            args=[
                'udevadm',
                'trigger',
                '--subsystem-match=block',
                '--action=add',
                ],
            )
        if ret[0]:
            return ret
    return (0, '', '', '')


def activate_disk(cluster, disk, init):
    """
    Run on the osd node, activates a disk.
    """
    def subproc_call(*args, **kwargs):
        """
        call subproc that might fail, collect returncode and stderr/stdout
        to be used in pushy.compile()d functions.  Returns 4-tuple of
        (process exit code, command, stdout contents, stderr contents)
        """
        import subprocess
        import tempfile

        otmp = tempfile.TemporaryFile()
        etmp = tempfile.TemporaryFile()
        cmd = ' '.join(kwargs['args'])
        ret = 0
        errtxt = ''
        kwargs.update(dict(stdout=otmp, stderr=etmp))
        try:
            subprocess.check_call(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            ret = e.returncode
        except Exception as e:
            ret = -1
            # OSError has errno
            if hasattr(e, 'errno'):
                ret = e.errno
            errtxt = str(e)
        otmp.seek(0)
        etmp.seek(0)
        return (ret, cmd, otmp.read(), errtxt + etmp.read())

    return subproc_call(
        args=[
            'ceph-disk-activate',
            '--mark-init',
            init,
            '--mount',
            disk,
            ])

def prepare(args, cfg, activate_prepared_disk):
    LOG.debug(
        'Preparing cluster %s disks %s',
        args.cluster,
        ' '.join(':'.join(x or '' for x in t) for t in args.disk),
        )

    key = get_bootstrap_osd_key(cluster=args.cluster)

    bootstrapped = set()
    errors = 0
    for hostname, disk, journal in args.disk:
        try:
            if disk is None:
                raise exc.NeedDiskError(hostname)
            # TODO username
            sudo = args.pushy(get_transport(hostname))

            if hostname not in bootstrapped:
                bootstrapped.add(hostname)
                LOG.debug('Deploying osd to %s', hostname)

                write_conf_r = sudo.compile(conf.write_conf)
                conf_data = StringIO()
                cfg.write(conf_data)
                write_conf_r(
                    cluster=args.cluster,
                    conf=conf_data.getvalue(),
                    overwrite=args.overwrite_conf,
                    )

                create_osd_r = sudo.compile(create_osd)
                ret, cmd, out, err = create_osd_r(
                    cluster=args.cluster,
                    key=key,
                    )
                if ret:
                    s = '{cmd} returned {ret}\n{out}\n{err}'.format(
                        cmd=cmd, ret=ret, out=out, err=err)
                    LOG.debug('Failed preparing host %s: %s', hostname, s)
                    raise RuntimeError(s)
                else:
                    LOG.debug('Host %s is now ready for osd use.', hostname)

            LOG.debug('Preparing host %s disk %s journal %s activate %s',
                      hostname, disk, journal, activate_prepared_disk)

            prepare_disk_r = sudo.compile(prepare_disk)
            ret, cmd, out, err = prepare_disk_r(
                cluster=args.cluster,
                disk=disk,
                journal=journal,
                activate_prepared_disk=activate_prepared_disk,
                zap=args.zap_disk,
                dmcrypt=args.dmcrypt,
                dmcrypt_dir=args.dmcrypt_key_dir,
                )
            sudo.close()
            if ret:
                s = '{cmd} returned {ret}\n{out}\n{err}'.format(
                    cmd=cmd, ret=ret, out=out, err=err)
                raise RuntimeError(s)
        except RuntimeError as e:
            LOG.error(e)
            errors += 1

    if errors:
        raise exc.GenericError('Failed to create %d OSDs' % errors)

def activate(args, cfg):
    LOG.debug(
        'Activating cluster %s disks %s',
        args.cluster,
        # join elements of t with ':', t's with ' '
        # allow None in elements of t; print as empty
        ' '.join(':'.join((s or '') for s in t) for t in args.disk),
        )

    for hostname, disk, journal in args.disk:

        # TODO username
        sudo = args.pushy(get_transport(hostname))

        LOG.debug('Activating host %s disk %s', hostname, disk)

        (distro, release, codename) = lsb.get_lsb_release(sudo)
        init = lsb.choose_init(distro, codename)
        LOG.debug('Distro %s codename %s, will use %s',
                  distro, codename, init)

        activate_disk_r = sudo.compile(activate_disk)
        err, cmd, stdout, stderr = activate_disk_r(
            cluster=args.cluster,
            disk=disk,
            init=init,
            )
        sudo.close()
        if err:
            s = '{cmd} returned {ret}\n{out}\n{err}'.format(
                cmd=cmd, ret=ret, out=out, err=err)
            raise RuntimeError(s)

# NOTE: this mirrors ceph-disk-prepare --zap-disk DEV
def zap(dev):
    import subprocess

    try:
        # this kills the crab
        #
        # sgdisk will wipe out the main copy of the GPT partition
        # table (sorry), but it doesn't remove the backup copies, and
        # subsequent commands will continue to complain and fail when
        # they see those.  zeroing the last few blocks of the device
        # appears to do the trick.
        lba_size = 4096
        size = 33 * lba_size
        with file(dev, 'wb') as f:
            f.seek(-size, os.SEEK_END)
            f.write(size*'\0')

        subprocess.check_call(
            args=[
                'sgdisk',
                '--zap-all',
                '--clear',
                '--mbrtogpt',
                '--',
                dev,
                ],
            )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e)


def disk_zap(args):
    cfg = conf.load(args)

    for hostname, disk, journal in args.disk:
        if not disk or not hostname:
            raise RuntimeError('zap command needs both HOSTNAME and DISK but got "%s %s"' % (hostname, disk))
        LOG.debug('zapping %s on %s', disk, hostname)

        # TODO username
        sudo = args.pushy(get_transport(hostname))
        zap_r = sudo.compile(zap)
        zap_r(disk)
        sudo.close()


def list_disk(conn, logger):
    check_call(
        conn,
        logger,
        [
            'ceph-disk',
            'list',
        ],
    )


def disk_list(args, cfg):
    for hostname, disk, journal in args.disk:
        distro = hosts.get(hostname)
        LOG.info(
            'Distro info: %s %s %s',
            distro.name,
            distro.release,
            distro.codename
        )
        rlogger = logging.getLogger(hostname)

        # TODO username
        LOG.debug('Listing disks on {hostname}...'.format(hostname=hostname))

        list_disk(distro.sudo_conn, rlogger)
        distro.sudo_conn.close()


def osd_list(args, cfg):
    LOG.error('Not yet implemented; see http://tracker.ceph.com/issues/5071')
    sys.exit(1)

def osd(args):
    cfg = conf.load(args)

    if args.subcommand == 'list':
        osd_list(args, cfg)
    elif args.subcommand == 'prepare':
        prepare(args, cfg, activate_prepared_disk=False)
    elif args.subcommand == 'create':
        prepare(args, cfg, activate_prepared_disk=True)
    elif args.subcommand == 'activate':
        activate(args, cfg)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)



def disk(args):
    cfg = conf.load(args)

    if args.subcommand == 'list':
        disk_list(args, cfg)
    elif args.subcommand == 'prepare':
        prepare(args, cfg, activate_prepared_disk=False)
    elif args.subcommand == 'activate':
        activate(args, cfg)
    elif args.subcommand == 'zap':
        disk_zap(args)
    else:
        LOG.error('subcommand %s not implemented', args.subcommand)
        sys.exit(1)


def colon_separated(s):
    journal = None
    disk = None
    host = None
    if s.count(':') == 2:
        (host, disk, journal) = s.split(':')
    elif s.count(':') == 1:
        (host, disk) = s.split(':')
    elif s.count(':') == 0:
        (host) = s
    else:
        raise argparse.ArgumentTypeError('must be in form HOST:DISK[:JOURNAL]')

    if disk:
        # allow just "sdb" to mean /dev/sdb
        disk = os.path.join('/dev', disk)
        if journal is not None:
            journal = os.path.join('/dev', journal)

    return (host, disk, journal)


@priority(50)
def make(parser):
    """
    Prepare a data disk on remote host.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'list',
            'create',
            'prepare',
            'activate',
            'destroy',
            ],
        help='list, create (prepare+activate), prepare, activate, or destroy',
        )
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK[:JOURNAL]',
        type=colon_separated,
        help='host and disk to prepare',
        )
    parser.add_argument(
        '--zap-disk',
        action='store_true', default=None,
        help='destroy existing partition table and content for DISK',
        )
    parser.add_argument(
        '--dmcrypt',
        action='store_true', default=None,
        help='use dm-crypt on DISK',
        )
    parser.add_argument(
        '--dmcrypt-key-dir',
        metavar='KEYDIR',
        default='/etc/ceph/dmcrypt-keys',
        help='directory where dm-crypt keys are stored',
        )
    parser.set_defaults(
        func=osd,
        )


@priority(50)
def make_disk(parser):
    """
    Manage disks on a remote host.
    """
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'list',
            'prepare',
            'activate',
            'zap',
            ],
        help='list, prepare, activate, zap',
        )
    parser.add_argument(
        'disk',
        nargs='+',
        metavar='HOST:DISK',
        type=colon_separated,
        help='host and disk to zap',
        )
    parser.add_argument(
        '--zap-disk',
        action='store_true', default=None,
        help='destroy existing partition table and content for DISK',
        )
    parser.add_argument(
        '--dmcrypt',
        action='store_true', default=None,
        help='use dm-crypt on DISK',
        )
    parser.add_argument(
        '--dmcrypt-key-dir',
        metavar='KEYDIR',
        default='/etc/ceph/dmcrypt-keys',
        help='directory where dm-crypt keys are stored',
        )
    parser.set_defaults(
        func=disk,
        )
