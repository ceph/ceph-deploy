import argparse
import re


ALPHANUMERIC_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*$')


def alphanumeric(s):
    """
    Enforces string to be alphanumeric with leading alpha.
    """
    if not ALPHANUMERIC_RE.match(s):
        raise argparse.ArgumentTypeError(
            'argument must start with a letter and contain only letters and numbers',
            )
    return s
