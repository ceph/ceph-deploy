import ConfigParser
import contextlib
from collections import OrderedDict
from StringIO import StringIO

from ceph_deploy import exc


class _TrimIndentFile(object):
    def __init__(self, fp):
        self.fp = fp

    def readline(self):
        line = self.fp.readline()
        return line.lstrip(' \t')


class CephConf(ConfigParser.RawConfigParser):
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
            return ConfigParser.RawConfigParser.get(self, section, key)
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            return None


def parse(fp):
    cfg = CephConf(dict_type=OrderedDict)
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
        f = file(path)
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


def match(conf_data, path):
    with file(path, 'rb') as f:
        conf = parse(f)
        data = StringIO()
        conf.write(data)
        return data.getvalue() == conf_data
