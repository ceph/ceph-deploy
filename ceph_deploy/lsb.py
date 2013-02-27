
def lsb_release():
    import subprocess

    args = [
        'lsb_release',
        '-s',
        '-i',
        '-r',
        '-c',
        ]
    p = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    out = p.stdout.read()
    ret = p.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=out)

    try:
        (distro, release, codename, empty) = out.split('\n', 3)
    except ValueError:
        raise RuntimeError('lsb_release gave invalid output')
    if empty != '':
        raise RuntimeError('lsb_release gave invalid output')
    return (distro, release, codename)


def choose_init(distro, codename):
    if distro == 'Ubuntu':
        return 'upstart'
    return 'sysvinit'
