
def get_file(path):
    """
    Run on mon node, grab a file.
    """
    try:
        with file(path, 'rb') as f:
            return f.read()
    except IOError:
        pass

