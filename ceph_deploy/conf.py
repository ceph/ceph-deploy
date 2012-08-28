import ConfigParser


class _TrimIndentFile(object):
    def __init__(self, fp):
        self.fp = fp

    def readline(self):
        line = self.fp.readline()
        return line.lstrip(' \t')


def parse(fp):
    cfg = ConfigParser.RawConfigParser()
    ifp = _TrimIndentFile(fp)
    cfg.readfp(ifp)
    return cfg
