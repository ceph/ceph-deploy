
def mon_hosts(mons):
    """
    Iterate through list of MON hosts, return tuples of (name, host).
    """
    for m in mons:
        if m.count(':'):
            (name, host) = m.split(':')
        else:
            name = m
            host = m
            if name.count('.') > 0:
                name = name.split('.')[0]
        yield (name, host)

def remote_shortname(socket):
    """
    Obtains remote hostname of the socket and cuts off the domain part
    of its FQDN.
    """
    return socket.gethostname().split('.', 1)[0]

