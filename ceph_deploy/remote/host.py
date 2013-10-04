"""
Collection of remote functions that are specific to a given platform
"""
import platform


def platform_information():
    """ detect platform information from remote host """
    distro, release, codename = platform.linux_distribution()
    return (
        str(distro).rstrip(),
        str(release).rstrip(),
        str(codename).rstrip()
    )


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
