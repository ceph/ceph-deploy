

def fake_getaddrinfo(*a, **kw):
    return_host = kw.get('return_host', 'host1')
    return [[0,0,0,0, return_host]]
