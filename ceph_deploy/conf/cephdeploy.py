from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError
import logging
import os
from os import path
import re

logger = logging.getLogger('ceph_deploy.conf')

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

# yum repos:
# [myrepo]
# baseurl = https://user:pass@example.org/rhel6
# gpgurl = https://example.org/keys/release.asc
# default = True
# extra-repos = cephrepo  # will install the cephrepo file too
#
# [cephrepo]
# name=ceph repo noarch packages
# baseurl=http://ceph.com/rpm-emperor/el6/noarch
# enabled=1
# gpgcheck=1
# type=rpm-md
# gpgkey=https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/autobuild.asc

# apt repos:
# [myrepo]
# baseurl = https://user:pass@example.org/
# gpgurl = https://example.org/keys/release.asc
# default = True
# extra-repos = cephrepo  # will install the cephrepo file too
#
# [cephrepo]
# baseurl=http://ceph.com/rpm-emperor/el6/noarch
# gpgkey=https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/autobuild.asc
"""


def location():
    """
    Find and return the location of the ceph-deploy configuration file. If this
    file does not exist, create one in a default location.
    """
    return _locate_or_create()


def load():
    parser = Conf()
    parser.read(location())
    return parser


def _locate_or_create():
    home_config = path.expanduser('~/.cephdeploy.conf')
    # With order of importance
    locations = [
        path.join(os.getcwd(), 'cephdeploy.conf'),
        home_config,
    ]

    for location in locations:
        if path.exists(location):
            logger.debug('found configuration file at: %s' % location)
            return location
    logger.info('could not find configuration file, will create one in $HOME')
    create_stub(home_config)
    return home_config


def create_stub(_path=None):
    _path = _path or path.expanduser('~/.cephdeploy.conf')
    logger.debug('creating new configuration file: %s' % _path)
    with open(_path, 'w') as cd_conf:
        cd_conf.write(cd_conf_template)


def set_overrides(args, _conf=None):
    """
    Read the configuration file and look for ceph-deploy sections
    to set flags/defaults from the values found. This will alter the
    ``args`` object that is created by argparse.
    """
    # Get the subcommand name to avoid overwritting values from other
    # subcommands that are not going to be used
    subcommand = args.func.__name__
    command_section = 'ceph-deploy-%s' % subcommand
    conf = _conf or load()
    for section_name in conf.sections():
        if section_name in ['ceph-deploy-global', command_section]:
            override_subcommand(
                section_name,
                conf.items(section_name),
                args
            )
    return args


def override_subcommand(section_name, section_items, args):
    """
    Given a specific section in the configuration file that maps to
    a subcommand (except for the global section) read all the keys that are
    actual argument flags and slap the values for that one subcommand.

    Return the altered ``args`` object at the end.
    """
    # XXX We are not coercing here any int-like values, so if ArgParse
    # does that in the CLI we are totally non-compliant with that expectation
    for k, v, in section_items:
        setattr(args, k, v)
    return args


class Conf(SafeConfigParser):
    """
    Subclasses from SafeConfigParser to give a few helpers for the ceph-deploy
    configuration. Specifically, it addresses the need to work with custom
    sections that signal the usage of custom repositories.
    """

    reserved_sections = ['ceph-deploy-global', 'ceph-deploy-install']

    def get_safe(self, section, key, default=None):
        """
        Attempt to get a configuration value from a certain section
        in a ``cfg`` object but returning None if not found. Avoids the need
        to be doing try/except {ConfigParser Exceptions} every time.
        """
        try:
            return self.get(section, key)
        except (NoSectionError, NoOptionError):
            return default

    def get_repos(self):
        """
        Return all the repo sections from the config, excluding the ceph-deploy
        reserved sections.
        """
        return [
            section for section in self.sections()
            if section not in self.reserved_sections
        ]

    @property
    def has_repos(self):
        """
        boolean to reflect having (or not) any repository sections
        """
        for section in self.sections():
            if section not in self.reserved_sections:
                return True
        return False

    def get_list(self, section, key):
        """
        Assumes that the value for a given key is going to be a list
        separated by commas. It gets rid of trailing comments.
        If just one item is present it returns a list with a single item, if no
        key is found an empty list is returned.
        """
        value = self.get_safe(section, key, [])
        if value == []:
            return value

        # strip comments
        value = re.split(r'\s+#', value)[0]

        # split on commas
        value = value.split(',')

        # strip spaces
        return [x.strip() for x in value]

    def get_default_repo(self):
        """
        Go through all the repositories defined in the config file and search
        for a truthy value for the ``default`` key. If there isn't any return
        None.
        """
        for repo in self.get_repos():
            if self.get_safe(repo, 'default') and self.getboolean(repo, 'default'):
                return repo
        return False
