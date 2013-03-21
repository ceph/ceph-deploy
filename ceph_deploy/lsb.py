
def lsb_release():
    import subprocess

    args = [ 'which', 'lsb_release', ]
    process = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    distro, _ = process.communicate()
    ret = process.wait()
    if ret != 0:
        raise RuntimeError('lsb_release not found on host')

    args = [ 'lsb_release', '-s', '-i' ]
    process = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    distro, _ = process.communicate()
    ret = process.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=distro)
    if distro == '':
        raise RuntimeError('lsb_release gave invalid output for distro')

    args = [ 'lsb_release', '-s', '-r', ]
    process = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    release, _ = process.communicate()
    ret = process.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=release)
    if release == '':
        raise RuntimeError('lsb_release gave invalid output for release')

    args = [ 'lsb_release', '-s', '-c', ]
    process = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    codename, _ = process.communicate()
    ret = process.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=codename)
    if codename == '':
        raise RuntimeError('lsb_release gave invalid output for codename')

    return (str(distro).rstrip(), str(release).rstrip(), str(codename).rstrip())


def choose_init(distro, codename):
    if distro == 'Ubuntu':
        return 'upstart'
    return 'sysvinit'
