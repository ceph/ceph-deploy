from ceph_deploy.util import constants

def url(key_type):
    return "%s%s.asc" % (constants.gpg_key_base_url, key_type)
