class DeployError(Exception):
    """
    Unknown deploy error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class ClusterExistsError(DeployError):
    """
    Cluster config exists already
    """
