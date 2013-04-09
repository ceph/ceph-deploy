from . import exc

def check_lsb_release():
    """
    Verify if lsb_release command is available
    """
    import subprocess

    args = [ 'which', 'lsb_release', ]
    process = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE,
        )
    lsb_release_path, _ = process.communicate()
    ret = process.wait()
    if ret != 0:
        raise RuntimeError('The lsb_release command was not found on remote host.  Please install the lsb-release package.')

def lsb_release():
    """
    Get LSB release information from lsb_release.

    Returns truple with distro, release and codename. Otherwise
    the function raises an error (subprocess.CalledProcessError or
    RuntimeError).
    """
    import subprocess

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


def get_lsb_release(sudo):
    """
    Get LSB release information from lsb_release.

    Check if lsb_release is installed on the remote host and issue
    a message if not.  

    Returns truple with distro, release and codename. Otherwise
    the function raises an error (subprocess.CalledProcessError or
    RuntimeError).
    """
    try:
        check_lsb_release_r = sudo.compile(check_lsb_release)
        status = check_lsb_release_r()
    except RuntimeError as e:
        raise exc.MissingPackageError(e.message)

    lsb_release_r = sudo.compile(lsb_release)
    return lsb_release_r()


def choose_init(distro, codename):
    """
    Select a init system for a given distribution.

    Returns the name of a init system (upstart, sysvinit ...).
    """
    if distro == 'Ubuntu':
        return 'upstart'
    return 'sysvinit'
