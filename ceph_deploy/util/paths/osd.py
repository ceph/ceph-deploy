"""
Comosd paths for osd, based on the constant file paths defined in
``ceph_deploy.util.constants``.
All functions return a string representation of the absolute path
construction.
"""
from os.path import join
from ceph_deploy.util import constants


def base(cluster):
    cluster = "%s-" % cluster
    return join(constants.osd_path, cluster)
