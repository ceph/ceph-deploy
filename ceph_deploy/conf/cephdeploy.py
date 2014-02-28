import os
from os import path


cd_conf_template = """
"""


def location():
    return _locate_or_create()


def _locate_or_create():
    # With order of importance
    locations = [
        path.join(path.dirname(os.getcwd(), 'cephdeploy.conf')),
        path.expanduser('~/.cephdeploy.conf'),
    ]

    for location in locations:
        if path.exists(location):
            return location
    create_stub(path.expanduser('~/.cephdeploy.conf'))


def create_stub(_path=None):
    _path = _path or path.expanduser('~/.cephdeploy.conf')
    with open(_path) as cd_conf:
        cd_conf.write(cd_conf_template)
