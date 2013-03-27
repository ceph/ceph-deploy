import logging

def get_file(path):
    """
    Run on mon node, grab a file.
    """
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        pass

def get_logger(args=None):
    loglevel = logging.DEBUG

    log = logging.getLogger(__name__)
    log.setLevel(loglevel)

    fh = logging.FileHandler('{cluster}.log'.format(cluster=args.cluster))
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(loglevel)

    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)

    log.addHandler(ch)
    log.addHandler(fh)
    return log

