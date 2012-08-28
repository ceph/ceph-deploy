import ConfigParser


def parse(fp):
    cfg = ConfigParser.RawConfigParser()
    cfg.readfp(fp)
    return cfg
