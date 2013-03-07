def lsb_release():
    import subprocess

    args = [ 'which', 'lsb_release', ]
    p = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    distro = p.stdout.read()
    ret = p.wait()
    if ret != 0:
        raise RuntimeError('lsb_release not found on host')

    args = [ 'lsb_release', '-s', '-i' ]
    p = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    distro = p.stdout.read()
    ret = p.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=out)
    if distro == '':
        raise RuntimeError('lsb_release gave invalid output for distro')

    args = [ 'lsb_release', '-s', '-r', ]
    p = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    release = p.stdout.read()
    ret = p.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=out)
    if release == '':
        raise RuntimeError('lsb_release gave invalid output for release')

    args = [ 'lsb_release', '-s', '-c', ]
    p = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    codename = p.stdout.read()
    ret = p.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=out)
    if codename == '':
        raise RuntimeError('lsb_release gave invalid output for codename')

    return (distro.rstrip(), release.rstrip(), codename.rstrip())


def choose_init(distro, codename):
    if distro == 'Ubuntu':
        return 'upstart'
    return 'sysvinit'
