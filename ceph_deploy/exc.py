class DeployError(Exception):
    """
    Unknown deploy error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class UnableToResolveError(DeployError):
    """
    Unable to resolve host
    """


class ClusterExistsError(DeployError):
    """
    Cluster config exists already
    """


class ConfigError(DeployError):
    """
    Cannot load config
    """


class NeedHostError(DeployError):
    """
    No hosts specified to deploy to.
    """


class NeedMonError(DeployError):
    """
    Cannot find nodes with ceph-mon.
    """


class NeedDiskError(DeployError):
    """
    Must supply disk/path argument
    """


class UnsupportedPlatform(DeployError):
    """
    Platform is not supported
    """
    def __init__(self, distro, codename, release):
        self.distro = distro
        self.codename = codename
        self.release = release

    def __str__(self):
        return '{doc}: {distro} {codename} {release}'.format(
            doc=self.__doc__.strip(),
            distro=self.distro,
            codename=self.codename,
            release=self.release,
        )


class ExecutableNotFound(DeployError):
    """
    Could not locate executable
    """
    def __init__(self, executable, host):
        self.executable = executable
        self.host = host

    def __str__(self):
        return "{doc} '{executable}' make sure it is installed and available on {host}".format(
            doc=self.__doc__.strip(),
            executable=self.executable,
            host=self.host,
        )


class MissingPackageError(DeployError):
    """
    A required package or command is missing
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class GenericError(DeployError):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ClusterNameError(DeployError):
    """
    Problem encountered with custom cluster name
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class KeyNotFoundError(DeployError):
    """
    Could not find keyring file
    """
    def __init__(self, keyring, hosts):
        self.keyring = keyring
        self.hosts = hosts

    def __str__(self):
        return '{doc}: {keys}'.format(
            doc=self.__doc__.strip(),
            keys=', '.join(
                [self.keyring.format(hostname=host) +
                 " on host {hostname}".format(hostname=host)
                 for host in self.hosts]
            )
        )
