import os.path
import logging
import json
import tempfile
import shutil
import time

from ceph_deploy import hosts
from ceph_deploy.cliutil import priority
from ceph_deploy.lib import remoto
import ceph_deploy.util.paths.mon

LOG = logging.getLogger(__name__)


def _keyring_equivalent(keyring_one, keyring_two):
    """
    Check two keyrings are identical
    """
    def keyring_extract_key(file_path):
        """
        Cephx keyring files may or may not have white space before some lines.
        They may have some values in quotes, so a safe way to compare is to
        extract the key.
        """
        with open(file_path) as f:
            for line in f:
                content = line.strip()
                if len(content) == 0:
                    continue
                split_line = content.split('=')
                if split_line[0].strip() == 'key':
                    return "=".join(split_line[1:]).strip()
        raise RuntimeError("File '%s' is not a keyring" % file_path)
    key_one = keyring_extract_key(keyring_one)
    key_two = keyring_extract_key(keyring_two)
    return key_one == key_two


def keytype_path_to(args, keytype):
    """
    Get the local filename for a keyring type
    """
    if keytype == "admin":
        return '{cluster}.client.admin.keyring'.format(
            cluster=args.cluster)
    if keytype == "mon":
        return '{cluster}.mon.keyring'.format(
            cluster=args.cluster)
    return '{cluster}.bootstrap-{what}.keyring'.format(
            cluster=args.cluster,
            what=keytype)


def keytype_identity(keytype):
    """
    Get the keyring identity from keyring type.

    This is used in authentication with keyrings and generating keyrings.
    """
    ident_dict = {
        'admin' : 'client.admin',
        'mds' : 'client.bootstrap-mds',
        'osd' : 'client.bootstrap-osd',
        'rgw' : 'client.bootstrap-rgw',
        'mon' : 'mon.'
    }
    return ident_dict.get(keytype, None)


def keytype_capabilities(keytype):
    """
    Get the capabilities of a keyring from keyring type.
    """
    cap_dict = {
        'admin' : [
            'osd', 'allow *',
            'mds', 'allow *',
            'mon', 'allow *'
            ],
        'mds' : [
            'mon', 'allow profile bootstrap-mds'
            ],
        'osd' : [
            'mon', 'allow profile bootstrap-osd'
            ],
        'rgw': [
            'mon', 'allow profile bootstrap-rgw'
            ]
        }
    return cap_dict.get(keytype, None)


def gatherkeys_missing(args, distro, rlogger, keypath, keytype, dest_dir):
    """
    Get or create the keyring from the mon using the mon keyring by keytype and
    copy to dest_dir
    """
    arguments = [
        '/usr/bin/ceph',
        '--connect-timeout=25',
        '--cluster={cluster}'.format(
            cluster=args.cluster),
        '--name', 'mon.',
        '--keyring={keypath}'.format(
            keypath=keypath),
        'auth', 'get-or-create',
        ]
    identity = keytype_identity(keytype)
    if identity is None:
        raise RuntimeError('Could not find identity for keytype:%s' % keytype)
    arguments.append(identity)
    capabilites = keytype_capabilities(keytype)
    if capabilites is None:
        raise RuntimeError('Could not find capabilites for keytype:%s' % keytype)
    arguments.extend(capabilites)
    out, err, code = remoto.process.check(
        distro.conn,
        arguments
        )
    if code != 0:
        rlogger.error('"ceph auth get-or-create for keytype %s returned %s', keytype, code)
        for line in err:
            rlogger.debug(line)
        return False
    keyring_name_local = keytype_path_to(args, keytype)
    keyring_path_local = os.path.join(dest_dir, keyring_name_local)
    with open(keyring_path_local, 'wb') as f:
        for line in out:
            f.write(line + b'\n')
    return True


def gatherkeys_with_mon(args, host, dest_dir):
    """
    Connect to mon and gather keys if mon is in quorum.
    """
    distro = hosts.get(host, username=args.username)
    remote_hostname = distro.conn.remote_module.shortname()
    dir_keytype_mon = ceph_deploy.util.paths.mon.path(args.cluster, remote_hostname)
    path_keytype_mon = "%s/keyring" % (dir_keytype_mon)
    mon_key = distro.conn.remote_module.get_file(path_keytype_mon)
    if mon_key is None:
        LOG.warning("No mon key found in host: %s", host)
        return False
    mon_name_local = keytype_path_to(args, "mon")
    mon_path_local = os.path.join(dest_dir, mon_name_local)
    with open(mon_path_local, 'wb') as f:
        f.write(mon_key)
    rlogger = logging.getLogger(host)
    path_asok = ceph_deploy.util.paths.mon.asok(args.cluster, remote_hostname)
    out, err, code = remoto.process.check(
        distro.conn,
            [
                "/usr/bin/ceph",
                "--connect-timeout=25",
                "--cluster={cluster}".format(
                    cluster=args.cluster),
                "--admin-daemon={asok}".format(
                    asok=path_asok),
                "mon_status"
            ]
        )
    if code != 0:
        rlogger.error('"ceph mon_status %s" returned %s', host, code)
        for line in err:
            rlogger.debug(line)
        return False
    try:
        mon_status = json.loads(b''.join(out).decode('utf-8'))
    except ValueError:
        rlogger.error('"ceph mon_status %s" output was not json', host)
        for line in out:
            rlogger.error(line)
        return False
    mon_number = None
    mon_map = mon_status.get('monmap')
    if mon_map is None:
        rlogger.error("could not find mon map for mons on '%s'", host)
        return False
    mon_quorum = mon_status.get('quorum')
    if mon_quorum is None:
        rlogger.error("could not find quorum for mons on '%s'" , host)
        return False
    mon_map_mons = mon_map.get('mons')
    if mon_map_mons is None:
        rlogger.error("could not find mons in monmap on '%s'", host)
        return False
    for mon in mon_map_mons:
        if mon.get('name') == remote_hostname:
           mon_number = mon.get('rank')
           break
    if mon_number is None:
        rlogger.error("could not find '%s' in monmap", remote_hostname)
        return False
    if not mon_number in mon_quorum:
        rlogger.error("Not yet quorum for '%s'", host)
        return False
    for keytype in ["admin", "mds", "osd", "rgw"]:
        if not gatherkeys_missing(args, distro, rlogger, path_keytype_mon, keytype, dest_dir):
            # We will return failure if we fail to gather any key
            rlogger.error("Failed to return '%s' key from host ", keytype, host)
            return False
    return True


def gatherkeys(args):
    """
    Gather keys from any mon and store in current working directory.

    Backs up keys from previous installs and stores new keys.
    """
    oldmask = os.umask(0o77)
    try:
        try:
            tmpd = tempfile.mkdtemp()
            LOG.info("Storing keys in temp directory %s", tmpd)
            sucess = False
            for host in args.mon:
                sucess = gatherkeys_with_mon(args, host, tmpd)
                if sucess:
                    break
            if not sucess:
                LOG.error("Failed to connect to host:%s" ,', '.join(args.mon))
                raise RuntimeError('Failed to connect any mon')
            had_error = False
            date_string = time.strftime("%Y%m%d%H%M%S")
            for keytype in ["admin", "mds", "mon", "osd", "rgw"]:
                filename = keytype_path_to(args, keytype)
                tmp_path = os.path.join(tmpd, filename)
                if not os.path.exists(tmp_path):
                    LOG.error("No key retrived for '%s'" , keytype)
                    had_error = True
                    continue
                if not os.path.exists(filename):
                    LOG.info("Storing %s" % (filename))
                    shutil.move(tmp_path, filename)
                    continue
                if _keyring_equivalent(tmp_path, filename):
                    LOG.info("keyring '%s' already exists" , filename)
                    continue
                backup_keyring = "%s-%s" % (filename, date_string)
                LOG.info("Replacing '%s' and backing up old key as '%s'", filename, backup_keyring)
                shutil.copy(filename, backup_keyring)
                shutil.move(tmp_path, filename)
            if had_error:
                raise RuntimeError('Failed to get all key types')
        finally:
            LOG.info("Destroy temp directory %s" %(tmpd))
            shutil.rmtree(tmpd)
    finally:
        os.umask(oldmask)


@priority(40)
def make(parser):
    """
    Gather authentication keys for provisioning new nodes.
    """
    parser.add_argument(
        'mon',
        metavar='HOST',
        nargs='+',
        help='monitor host to pull keys from',
        )
    parser.set_defaults(
        func=gatherkeys,
        )
