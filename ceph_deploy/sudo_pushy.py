import pushy.transport.ssh


class SshSudoTransport(object):
    @staticmethod
    def Popen(command, *a, **kw):
        command = ['sudo'] + command
        return pushy.transport.ssh.Popen(command, *a, **kw)


def patch():
    """
    Monkey patches pushy so it supports running via (passphraseless)
    sudo on the remote host.
    """
    pushy.transports['ssh+sudo'] = SshSudoTransport
