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
    def __init__(self, distro, codename):
        self.distro = distro
        self.codename = codename

    def __str__(self):
        return '{doc}: {distro} {codename}'.format(
            doc=self.__doc__.strip(),
            distro=self.distro,
            codename=self.codename,
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
