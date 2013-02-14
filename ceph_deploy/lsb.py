
def lsb_release():
    import platform
    out = platform.dist()

    try:
        (distro, release, codename) = out
    except ValueError:
        raise RuntimeError('platform.dist() gave invalid output')
    if distro == '':
        raise RuntimeError('platform.dist() gave invalid output')

    return (distro, release, codename)

def choose_init(distro, codename):
    if distro == 'Ubuntu':
        return 'upstart'
    return 'sysvinit'
