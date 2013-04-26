import pushy.transport.ssh
import pushy.transport.local
import subprocess 

def __init__(self, command, address, **kwargs):
    pushy.transport.BaseTransport.__init__(self, address)

    self.__proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   bufsize=65535)

    self.stdout = self.__proc.stdout
    self.stderr = self.__proc.stderr
    self.stdin  = self.__proc.stdin

class SshSudoTransport(object):
    @staticmethod
    def Popen(command, *a, **kw):
        command = ['sudo'] + command
        return pushy.transport.ssh.Popen(command, *a, **kw)

class LocalSudoTransport(object):
    @staticmethod
    def Popen(command, *a, **kw):
        command = ['sudo'] + command
        # Overide the original initializer
        pushy.transport.local.Popen.__init__ = __init__
        return pushy.transport.local.Popen(command, *a, **kw)

def get_transport(hostname):
    import socket

    myhostname = socket.gethostname().split('.')[0]
    if hostname == myhostname:
        return 'local+sudo:'
    else:
        return 'ssh+sudo:{hostname}'.format(hostname=hostname)

def patch():
    """
    Monkey patches pushy so it supports running via (passphraseless)
    sudo on the remote host.
    """
    pushy.transports['ssh+sudo'] = SshSudoTransport
    pushy.transports['local+sudo'] = LocalSudoTransport
