from ceph_deploy import exc
import logging
import re
import socket
from ceph_deploy.lib import remoto


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


def in_subnet(cidr, addrs=None):
    """
    Returns True if host is within specified subnet, otherwise False
    """
    for address in addrs:
        if ip_in_subnet(address, cidr):
            return True
    return False


def ip_addresses(conn, interface=None, include_loopback=False):
    """
    Returns a list of IPv4 addresses assigned to the host. 127.0.0.1 is
    ignored, unless 'include_loopback=True' is indicated. If 'interface' is
    provided, then only IP addresses from that interface will be returned.

    Example output looks like::

        >>> ip_addresses(conn)
        >>> ['192.168.1.111', '10.0.1.12']

    """
    ret = set()
    ifaces = linux_interfaces(conn)
    if interface is None:
        target_ifaces = ifaces
    else:
        target_ifaces = dict((k, v) for k, v in ifaces.items()
                             if k == interface)
        if not target_ifaces:
            LOG.error('Interface {0} not found.'.format(interface))
    for ipv4_info in target_ifaces.values():
        for ipv4 in ipv4_info.get('inet', []):
            loopback = in_subnet('127.0.0.0/8', [ipv4.get('address')]) or ipv4.get('label') == 'lo'
            if not loopback or include_loopback:
                ret.add(ipv4['address'])
        for secondary in ipv4_info.get('secondary', []):
            addr = secondary.get('address')
            if addr and secondary.get('type') == 'inet':
                if include_loopback or (not include_loopback and not in_subnet('127.0.0.0/8', [addr])):
                    ret.add(addr)
    if ret:
        conn.logger.debug('IP addresses found: %s' % str(list(ret)))
    return sorted(list(ret))


def linux_interfaces(conn):
    """
    Obtain interface information for *NIX/BSD variants in remote servers.

    Example output from a remote node with a couple of interfaces::

        {'eth0': {'hwaddr': '08:00:27:08:c2:e4',
                  'inet': [{'address': '10.0.2.15',
                            'broadcast': '10.0.2.255',
                            'label': 'eth0',
                            'netmask': '255.255.255.0'}],
                  'inet6': [{'address': 'fe80::a00:27ff:fe08:c2e4',
                             'prefixlen': '64'}],
                  'up': True},
         'eth1': {'hwaddr': '08:00:27:70:06:f1',
                  'inet': [{'address': '192.168.111.101',
                            'broadcast': '192.168.111.255',
                            'label': 'eth1',
                            'netmask': '255.255.255.0'}],
                  'inet6': [{'address': 'fe80::a00:27ff:fe70:6f1',
                             'prefixlen': '64'}],
                  'up': True},
         'lo': {'hwaddr': '00:00:00:00:00:00',
                'inet': [{'address': '127.0.0.1',
                          'broadcast': None,
                          'label': 'lo',
                          'netmask': '255.0.0.0'}],
                'inet6': [{'address': '::1', 'prefixlen': '128'}],
                'up': True}}

    :param conn: A connection object to a remote node
    """
    ifaces = dict()
    ip_path = conn.remote_module.which('ip')
    ifconfig_path = None if ip_path else conn.remote_module.which('ifconfig')
    if ip_path:
        cmd1, _, _ = remoto.process.check(
            conn,
            [
                '{0}'.format(ip_path),
                'link',
                'show',
            ],
        )
        cmd2, _, _ = remoto.process.check(
            conn,
            [
                '{0}'.format(ip_path),
                'addr',
                'show',
            ],
        )
        ifaces = _interfaces_ip(b'\n'.join(cmd1).decode('utf-8') + '\n' +
                                b'\n'.join(cmd2).decode('utf-8'))
    elif ifconfig_path:
        cmd, _, _ = remoto.process.check(
            conn,
            [
                '{0}'.format(ifconfig_path),
                '-a',
            ]
        )
        ifaces = _interfaces_ifconfig('\n'.join(cmd))
    return ifaces


def _interfaces_ip(out):
    """
    Uses ip to return a dictionary of interfaces with various information about
    each (up/down state, ip address, netmask, and hwaddr)
    """
    ret = dict()

    def parse_network(value, cols):
        """
        Return a tuple of ip, netmask, broadcast
        based on the current set of cols
        """
        brd = None
        if '/' in value:  # we have a CIDR in this address
            ip, cidr = value.split('/')  # pylint: disable=C0103
        else:
            ip = value  # pylint: disable=C0103
            cidr = 32

        if type_ == 'inet':
            mask = cidr_to_ipv4_netmask(int(cidr))
            if 'brd' in cols:
                brd = cols[cols.index('brd') + 1]
        elif type_ == 'inet6':
            mask = cidr
        return (ip, mask, brd)

    groups = re.compile('\r?\n\\d').split(out)
    for group in groups:
        iface = None
        data = dict()

        for line in group.splitlines():
            if ' ' not in line:
                continue
            match = re.match(r'^\d*:\s+([\w.\-]+)(?:@)?([\w.\-]+)?:\s+<(.+)>', line)
            if match:
                iface, parent, attrs = match.groups()
                if 'UP' in attrs.split(','):
                    data['up'] = True
                else:
                    data['up'] = False
                if parent:
                    data['parent'] = parent
                continue

            cols = line.split()
            if len(cols) >= 2:
                type_, value = tuple(cols[0:2])
                iflabel = cols[-1:][0]
                if type_ in ('inet', 'inet6'):
                    if 'secondary' not in cols:
                        ipaddr, netmask, broadcast = parse_network(value, cols)
                        if type_ == 'inet':
                            if 'inet' not in data:
                                data['inet'] = list()
                            addr_obj = dict()
                            addr_obj['address'] = ipaddr
                            addr_obj['netmask'] = netmask
                            addr_obj['broadcast'] = broadcast
                            addr_obj['label'] = iflabel
                            data['inet'].append(addr_obj)
                        elif type_ == 'inet6':
                            if 'inet6' not in data:
                                data['inet6'] = list()
                            addr_obj = dict()
                            addr_obj['address'] = ipaddr
                            addr_obj['prefixlen'] = netmask
                            data['inet6'].append(addr_obj)
                    else:
                        if 'secondary' not in data:
                            data['secondary'] = list()
                        ip_, mask, brd = parse_network(value, cols)
                        data['secondary'].append({
                            'type': type_,
                            'address': ip_,
                            'netmask': mask,
                            'broadcast': brd,
                            'label': iflabel,
                        })
                        del ip_, mask, brd
                elif type_.startswith('link'):
                    data['hwaddr'] = value
        if iface:
            ret[iface] = data
            del iface, data
    return ret


def _interfaces_ifconfig(out):
    """
    Uses ifconfig to return a dictionary of interfaces with various information
    about each (up/down state, ip address, netmask, and hwaddr)
    """
    ret = dict()

    piface = re.compile(r'^([^\s:]+)')
    pmac = re.compile('.*?(?:HWaddr|ether|address:|lladdr) ([0-9a-fA-F:]+)')
    pip = re.compile(r'.*?(?:inet addr:|inet )(.*?)\s')
    pip6 = re.compile('.*?(?:inet6 addr: (.*?)/|inet6 )([0-9a-fA-F:]+)')
    pmask = re.compile(r'.*?(?:Mask:|netmask )(?:((?:0x)?[0-9a-fA-F]{8})|([\d\.]+))')
    pmask6 = re.compile(r'.*?(?:inet6 addr: [0-9a-fA-F:]+/(\d+)|prefixlen (\d+)).*')
    pupdown = re.compile('UP')
    pbcast = re.compile(r'.*?(?:Bcast:|broadcast )([\d\.]+)')

    groups = re.compile('\r?\n(?=\\S)').split(out)
    for group in groups:
        data = dict()
        iface = ''
        updown = False
        for line in group.splitlines():
            miface = piface.match(line)
            mmac = pmac.match(line)
            mip = pip.match(line)
            mip6 = pip6.match(line)
            mupdown = pupdown.search(line)
            if miface:
                iface = miface.group(1)
            if mmac:
                data['hwaddr'] = mmac.group(1)
            if mip:
                if 'inet' not in data:
                    data['inet'] = list()
                addr_obj = dict()
                addr_obj['address'] = mip.group(1)
                mmask = pmask.match(line)
                if mmask:
                    if mmask.group(1):
                        mmask = _number_of_set_bits_to_ipv4_netmask(
                            int(mmask.group(1), 16))
                    else:
                        mmask = mmask.group(2)
                    addr_obj['netmask'] = mmask
                mbcast = pbcast.match(line)
                if mbcast:
                    addr_obj['broadcast'] = mbcast.group(1)
                data['inet'].append(addr_obj)
            if mupdown:
                updown = True
            if mip6:
                if 'inet6' not in data:
                    data['inet6'] = list()
                addr_obj = dict()
                addr_obj['address'] = mip6.group(1) or mip6.group(2)
                mmask6 = pmask6.match(line)
                if mmask6:
                    addr_obj['prefixlen'] = mmask6.group(1) or mmask6.group(2)
                data['inet6'].append(addr_obj)
        data['up'] = updown
        ret[iface] = data
        del data
    return ret


def _number_of_set_bits_to_ipv4_netmask(set_bits):  # pylint: disable=C0103
    """
    Returns an IPv4 netmask from the integer representation of that mask.

    Ex. 0xffffff00 -> '255.255.255.0'
    """
    return cidr_to_ipv4_netmask(_number_of_set_bits(set_bits))


def _number_of_set_bits(x):
    """
    Returns the number of bits that are set in a 32bit int
    """
    #  Taken from http://stackoverflow.com/a/4912729. Many thanks!
    x -= (x >> 1) & 0x55555555
    x = ((x >> 2) & 0x33333333) + (x & 0x33333333)
    x = ((x >> 4) + x) & 0x0f0f0f0f
    x += x >> 8
    x += x >> 16
    return x & 0x0000003f


def cidr_to_ipv4_netmask(cidr_bits):
    """
    Returns an IPv4 netmask
    """
    try:
        cidr_bits = int(cidr_bits)
        if not 1 <= cidr_bits <= 32:
            return ''
    except ValueError:
        return ''

    netmask = ''
    for idx in range(4):
        if idx:
            netmask += '.'
        if cidr_bits >= 8:
            netmask += '255'
            cidr_bits -= 8
        else:
            netmask += '{0:d}'.format(256 - (2 ** (8 - cidr_bits)))
            cidr_bits = 0
    return netmask
