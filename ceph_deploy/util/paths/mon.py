"""
Common paths for mon, based on the constant file paths defined in
``ceph_deploy.util.constants``.
All functions return a string representation of the absolute path
construction.
"""
from os.path import join

from ceph_deploy.util import constants


def base(cluster):
    cluster = "%s-" % cluster
    return join(constants.mon_path, cluster)


def path(cluster, hostname):
    """
    Example usage::

        >>> mon.path('mycluster', 'hostname')
        /var/lib/ceph/mon/mycluster-myhostname
    """
    return "%s%s" % (base(cluster), hostname)


def done(cluster, hostname):
    """
    Example usage::

        >>> mon.done('mycluster', 'hostname')
        /var/lib/ceph/mon/mycluster-myhostname/done
    """
    return join(path(cluster, hostname), 'done')


def init(cluster, hostname, init):
    """
    Example usage::

        >>> mon.init('mycluster', 'hostname', 'init')
        /var/lib/ceph/mon/mycluster-myhostname/init
    """
    return join(path(cluster, hostname), init)


def keyring(cluster, hostname):
    """
    Example usage::

        >>> mon.keyring('mycluster', 'myhostname')
        /var/lib/ceph/tmp/mycluster-myhostname.mon.keyring
    """
    keyring_file = '%s-%s.mon.keyring' % (cluster, hostname)
    return join(constants.tmp_path, keyring_file)
