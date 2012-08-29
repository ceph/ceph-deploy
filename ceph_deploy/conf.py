import ConfigParser
import contextlib

from . import exc


class _TrimIndentFile(object):
    def __init__(self, fp):
        self.fp = fp

    def readline(self):
        line = self.fp.readline()
        return line.lstrip(' \t')


def _optionxform(s):
    s = s.replace('_', ' ')
    s = '_'.join(s.split())
    return s


def parse(fp):
    cfg = ConfigParser.RawConfigParser()
    cfg.optionxform = _optionxform
    ifp = _TrimIndentFile(fp)
    cfg.readfp(ifp)
    return cfg


def load(args):
    path = '{cluster}.conf'.format(cluster=args.cluster)
    try:
        f = file(path)
    except IOError as e:
        raise exc.ConfigError(e)
    else:
        with contextlib.closing(f):
            return parse(f)
