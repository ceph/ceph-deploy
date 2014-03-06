import os
from os import path


cd_conf_template = """
#
# ceph-deploy configuration file
#


"""


def location():
    """
    Find and return the location of the ceph-deploy configuration file. If this
    file does not exist, create one in a default location.
    """
    return _locate_or_create()


def _locate_or_create():
    home_config = path.expanduser('~/.cephdeploy.conf')
    # With order of importance
    locations = [
        path.join(path.dirname(os.getcwd()), 'cephdeploy.conf'),
        home_config,
    ]

    for location in locations:
        if path.exists(location):
            return location
    create_stub(home_config)
    return home_config


def create_stub(_path=None):
    _path = _path or path.expanduser('~/.cephdeploy.conf')
    with open(_path) as cd_conf:
        cd_conf.write(cd_conf_template)
