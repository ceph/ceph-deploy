from ceph_deploy.exc import ExecutableNotFound
from ceph_deploy.util import system, versions
from ceph_deploy.lib import remoto


class Ceph(object):
    """
    Determine different aspects of the Ceph package, like ``version`` and path
    ``executable``. Although mostly provide a version object that helps for
    parsing and comparing.
    """

    def __init__(self, conn, _check=None):
        self.conn = conn
        self._check = _check or remoto.process.check

    @property
    def installed(self):
        """
        If the ``ceph`` executable exists, then Ceph is installed. Should
        probably be revisited if different components do not have the ``ceph``
        executable (this is currently provided by ``ceph-common``).
        """
        return bool(self.executable)

    @property
    def executable(self):
        try:
            return system.executable_path(self.conn, 'ceph')
        except ExecutableNotFound:
            return None

    def _get_version_output(self):
        """
        Ignoring errors, call `ceph --version` and return only the version
        portion of the output. For example, output like::

            ceph version 9.0.1-1234kjd (asdflkj2k3jh234jhg)

        Would return::

            9.0.1-1234kjd
        """
        if not self.executable:
            return ''
        command = [self.executable, '--version']
        out, _, _ = self._check(self.conn, command)
        try:
            return out.decode('utf-8').split()[2]
        except IndexError:
            return ''

    @property
    def version(self):
        """
        Return a version object (see
        :mod:``ceph_deploy.util.versions.NormalizedVersion``)
        """
        return versions.parse_version(self._get_version_output)


# callback helpers

def ceph_is_installed(module):
    """
    A helper callback to be executed after the connection is made to ensure
    that Ceph is installed.
    """
    ceph_package = Ceph(module.conn)
    if not ceph_package.installed:
        host = module.conn.hostname
        raise RuntimeError(
            'ceph needs to be installed in remote host: %s' % host
        )
