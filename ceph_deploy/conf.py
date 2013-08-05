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


def write_conf(cluster, conf, overwrite):
    """ write cluster configuration to /etc/ceph/{cluster}.conf """
    import os

    path = '/etc/ceph/{cluster}.conf'.format(cluster=cluster)
    tmp = '{path}.{pid}.tmp'.format(path=path, pid=os.getpid())

    if os.path.exists(path):
        with file(path, 'rb') as f:
            old = f.read()
            if old != conf and not overwrite:
                raise RuntimeError('config file %s exists with different content; use --overwrite-conf to overwrite' % path)
    with file(tmp, 'w') as f:
        f.write(conf)
        f.flush()
        os.fsync(f)
    os.rename(tmp, path)
