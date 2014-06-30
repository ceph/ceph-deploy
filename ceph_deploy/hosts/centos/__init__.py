import mon  # noqa
import pkg  # noqa
from install import install, mirror_install, repo_install, repository_url_part, rpm_dist  # noqa
from uninstall import uninstall  # noqa

# Allow to set some information about this distro
#

distro = None
release = None
codename = None
