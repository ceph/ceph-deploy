from ceph_deploy import exc
import logging
import socket


LOG = logging.getLogger(__name__)


# TODO: at some point, it might be way more accurate to do this in the actual
# host where we need to get IPs from. SaltStack does this by calling `ip` and
# parsing the output, which is probably the one true way of dealing with it.

def get_nonlocal_ip(host, subnet=None):
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
        if subnet and ip_in_subnet(ip, subnet):
            LOG.info('found ip (%s) for host (%s) to be in cluster subnet (%s)' % (
                ip,
                host,
                subnet,)
            )

            return ip

        if not ip.startswith('127.'):
            if subnet:
                LOG.warning('could not match ip (%s) for host (%s) for cluster subnet (%s)' % (
                    ip,
                    host,
                    subnet,)
                )
            return ip
    raise exc.UnableToResolveError(host)


def ip_in_subnet(ip, subnet):
    """Does IP exists in a given subnet utility. Returns a boolean"""
    ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
    netstr, bits = subnet.split('/')
    netaddr = int(''.join(['%02x' % int(x) for x in netstr.split('.')]), 16)
    mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
    return (ipaddr & mask) == (netaddr & mask)
