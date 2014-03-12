import mon
from ceph_deploy.hosts.centos import pkg
from ceph_deploy.hosts.centos.install import repo_install
from install import install, mirror_install
from uninstall import uninstall

# Allow to set some information about this distro
#

distro = None
release = None
codename = None
