from ceph_deploy import exc
import socket


def get_nonlocal_ip(host):
    """
    Search result of getaddrinfo() for a non-localhost-net address
    """
    try:
        ailist = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise exc.UnableToResolveError(host)
    for ai in ailist:
        # an ai is a 5-tuple; the last element is (ip, port)
        ip = ai[4][0]
        if not ip.startswith('127.'):
            return ip
    raise exc.UnableToResolveError(host)
