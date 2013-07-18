from os.path import join

from ceph_deploy.util import constants


class mon(object):
    """
    Common paths for mon, based on the constant file paths defined in
    ``ceph_deploy.util.constants``.
    All classmethods return a string representation of the absolute path
    construction.
    """

    _base = join(constants.mon_path, 'ceph-')

    @classmethod
    def path(cls, cluster, hostname):
        """
        Example usage::

            >>> mon.path('mycluster', 'hostname')
            /var/lib/ceph/mon/mycluster-myhostname
        """
        return "%s%s" % (cls._base, hostname)

    @classmethod
    def done(cls, cluster, hostname):
        """
        Example usage::

            >>> mon.done('mycluster', 'hostname')
            /var/lib/ceph/mon/mycluster-myhostname/done
        """
        return join(cls.path(cluster, hostname), 'done')

    @classmethod
    def init(cls, cluster, hostname, init):
        """
        Example usage::

            >>> mon.init('mycluster', 'hostname', 'init')
            /var/lib/ceph/mon/mycluster-myhostname/init
        """
        return join(cls.path(cluster, hostname), init)

    @classmethod
    def keyring(cls, cluster, hostname):
        """
        Example usage::

            >>> mon.keyring('mycluster', 'myhostname')
            /var/lib/ceph/tmp/mycluster-myhostname.mon.keyring
        """
        keyring_file = '%s-%s.mon.keyring' % (cluster, hostname)
        return join(constants.tmp_path, keyring_file)
