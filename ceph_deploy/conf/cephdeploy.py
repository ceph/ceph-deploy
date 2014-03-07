from ConfigParser import SafeConfigParser
import os
from os import path


cd_conf_template = """
#
# ceph-deploy configuration file
#

[ceph-deploy-global]
# Overrides for some of ceph-deploy's global flags, like verbosity or cluster
# name

[ceph-deploy-install]
# Overrides for some of ceph-deploy's install flags, like version of ceph to
# install


#
# Repositories section
#

# [myrepo]
# repourl = https://user:pass@example.org/rhel6
# gpgurl = https://example.org/keys/release.asc
# default = True
# extra-repos = cephrepo  # Install the cephrepo file too
#
# [cephrepo]
# name=ceph repo noarch packages
# baseurl=http://ceph.com/rpm-emperor/el6/noarch
# enabled=1
# gpgcheck=1
# type=rpm-md
# gpgkey=https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/autobuild.asc
"""


def location():
    """
    Find and return the location of the ceph-deploy configuration file. If this
    file does not exist, create one in a default location.
    """
    return _locate_or_create()


def load():
    parser = SafeConfigParser()
    parser.read(location())
    return parser


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
    with open(_path, 'w') as cd_conf:
        cd_conf.write(cd_conf_template)
