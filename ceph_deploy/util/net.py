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


def ip_in_subnet(ip, subnet):
    """Does IP exists in a given subnet utility. Returns a boolean"""
    ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
    netstr, bits = subnet.split('/')
    netaddr = int(''.join(['%02x' % int(x) for x in netstr.split('.')]), 16)
    mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
    return (ipaddr & mask) == (netaddr & mask)
