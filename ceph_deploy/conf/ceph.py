try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import contextlib
import sys

from ceph_deploy import exc


class _TrimIndentFile(object):
    def __init__(self, fp):
        self.fp = fp

    def readline(self):
        line = self.fp.readline()
        return line.lstrip(' \t')

    def __iter__(self):
        return iter(self.readline, '')

class CephConf(configparser.RawConfigParser):
    def __init__(self, *args, **kwargs):
        if sys.version_info >= (3, 2):
            kwargs.setdefault('strict', False)
        # super() cannot be used with an old-style class
        configparser.RawConfigParser.__init__(self, *args, **kwargs)

    def optionxform(self, s):
        s = s.replace('_', ' ')
        s = '_'.join(s.split())
        return s

    def safe_get(self, section, key):
        """
        Attempt to get a configuration value from a certain section
        in a ``cfg`` object but returning None if not found. Avoids the need
        to be doing try/except {ConfigParser Exceptions} every time.
        """
        try:
            #Use full parent function so we can replace it in the class
            # if desired
            return configparser.RawConfigParser.get(self, section, key)
        except (configparser.NoSectionError,
                configparser.NoOptionError):
            return None


def parse(fp):
    cfg = CephConf()
    ifp = _TrimIndentFile(fp)
    cfg.readfp(ifp)
    return cfg


def load(args):
    """
    :param args: Will be used to infer the proper configuration name, or
    if args.ceph_conf is passed in, that will take precedence
    """
    path = args.ceph_conf or '{cluster}.conf'.format(cluster=args.cluster)

    try:
        f = open(path)
    except IOError as e:
        raise exc.ConfigError(
            "%s; has `ceph-deploy new` been run in this directory?" % e
        )
    else:
        with contextlib.closing(f):
            return parse(f)


def load_raw(args):
    """
    Read the actual file *as is* without parsing/modifiying it
    so that it can be written maintaining its same properties.

    :param args: Will be used to infer the proper configuration name
    :paran path: alternatively, use a path for any configuration file loading
    """
    path = args.ceph_conf or '{cluster}.conf'.format(cluster=args.cluster)
    try:
        with open(path) as ceph_conf:
            return ceph_conf.read()
    except (IOError, OSError) as e:
        raise exc.ConfigError(
            "%s; has `ceph-deploy new` been run in this directory?" % e
        )


def write_conf(cluster, conf, overwrite):
    """ write cluster configuration to /etc/ceph/{cluster}.conf """
    import os

    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp = '{path}.{pid}.tmp'.format(path=path, pid=os.getpid())

    if os.path.exists(path):
        with open(path) as f:
            old = f.read()
            if old != conf and not overwrite:
                raise RuntimeError('config file %s exists with different content; use --overwrite-conf to overwrite' % path)
    with open(tmp, 'w') as f:
        f.write(conf)
        f.flush()
        os.fsync(f)
    os.rename(tmp, path)
