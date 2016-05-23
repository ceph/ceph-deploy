

def generate_ips(start_ip, end_ip):
    start = list(map(int, start_ip.split(".")))
    end = list(map(int, end_ip.split(".")))
    temp = start
    ip_range = []

    ip_range.append(start_ip)
    while temp != end:
        start[3] += 1
        for i in (3, 2, 1):
            if temp[i] == 256:
                temp[i] = 0
                temp[i-1] += 1
        ip_range.append(".".join(map(str, temp)))

    return ip_range


class Empty(object):
    """
    A bare class, with explicit behavior for key/value items to be set at
    instantiation.
    """
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def assert_too_few_arguments(err):
    assert ("error: too few arguments" in err or
            "error: the following argument" in err)
