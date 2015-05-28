from ceph_deploy.util import constants

def url(key_type, protocol="https"):
    return "{protocol}://{url}{key_type}.asc".format(
        protocol=protocol,
        url=constants.gpg_key_base_url,
        key_type=key_type
    )
