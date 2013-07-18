from os.path import join

from ceph_deploy.util import constants


class mon(object):

    _base = join(constants.mon_path, 'ceph-')

    @classmethod
    def path(cls, hostname):
        return "%s%s" % (cls._base, hostname)

    @classmethod
    def done(cls, hostname):
        return join(cls.path(hostname), 'done')

    @classmethod
    def init(cls, hostname, init):
        return join(cls.path(hostname), init)

    @classmethod
    def keyring(cls, cluster, hostname):
        keyring_file = '%s-%s.mon.keyring' % (cluster, hostname)
        return join(constants.tmp_path, keyring_file)
