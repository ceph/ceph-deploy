import socket
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


class Hostname(object):
    """
    Checks wether a given hostname is resolvable in DNS, otherwise raising and
    argparse error.
    """

    def __init__(self, _socket=None):
        self.socket = _socket or socket  # just used for testing

    def __call__(self, string):
        parts = string.split(':', 1)
        name = parts[0]
        host = parts[-1]
        try:
            self.socket.getaddrinfo(host, 0)
        except self.socket.gaierror:
            msg = "hostname: %s is not resolvable" % host
            raise argparse.ArgumentError(None, msg)

        try:
            self.socket.getaddrinfo(name, 0, 0, 0, 0, self.socket.AI_NUMERICHOST)
        except self.socket.gaierror:
            return string  # not an IP
        else:
            msg = '%s must be a hostname not an IP' % name
            raise argparse.ArgumentError(None, msg)

        return string
