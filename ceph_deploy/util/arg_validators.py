import argparse
import re


class RegexMatch(object):
    """
    Performs regular expression match on value.
    If the regular expression pattern matches it will it will return an error
    message that will work with argparse.
    """

    def __init__(self, pattern, statement=None):
        self.string_pattern = pattern
        self.pattern = re.compile(pattern)
        self.statement = statement
        if not self.statement:
            self.statement = "must match pattern %s" % self.string_pattern

    def __call__(self, string):
        match = self.pattern.search(string)
        if match:
            raise argparse.ArgumentError(None, self.statement)
        return string
