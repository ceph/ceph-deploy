"""
Common paths for osd, based on the constant file paths defined in
``ceph_deploy.util.constants``.
All functions return a string representation of the absolute path
construction.

Currently only care about the base osd path.
"""
from ceph_deploy.util import constants


def base():
    return constants.osd_path
