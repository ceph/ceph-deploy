.. _conf:

Ceph Deploy Configuration
=========================
Starting with version 1.4, ceph-deploy uses a configuration file that can be
one of:

* ``cephdeploy.conf`` (in the current directory)
* ``$HOME/.cephdeploy.conf`` (hidden in the user's home directory)

This configuration file allows for setting certain ceph-deploy behavior that
would be difficult to set on the command line or that it might be cumbersome to
do.

The file itself follows the INI style of configurations which means that it
consists of sections (in brackets) that may contain any number of key/value
pairs.

If a configuration file is not found in the current working directory nor in
the user's home dir, ceph-deploy will proceed to create one in the home
directory.

This is how a default configuration file would look like::

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
    # gpgkey=https://download.ceph.com/keys/release.asc

    # apt repos:
    # [myrepo]
    # baseurl = https://user:pass@example.org/
    # gpgurl = https://example.org/keys/release.asc
    # default = True
    # extra-repos = cephrepo  # will install the cephrepo file too
    #
    # [cephrepo]
    # baseurl=http://ceph.com/rpm-emperor/el6/noarch
    # gpgkey=https://download.ceph.com/keys/release.asc

.. conf_sections:

Sections
--------
To work with ceph-deploy configurations, it is important to note that all
sections that relate to ceph-deploy's flags and state are prefixed with
``ceph-deploy-`` followed by the subcommand or by ``global`` if it is something
that belongs to the global flags.

Any other section that is not prefixed with ``ceph-deploy-`` is considered
a repository.

Repositories can be very complex to describe and most of the time (specially
for yum repositories) they can be very verbose too.

Setting Default Flags or Values
-------------------------------
Because the configuration loading allows specifying the same flags as in the
CLI it is possible to set defaults. For example, assuming that a user always
wants to install Ceph the following way (that doesn't create/modify remote repo
files)::

    ceph-deploy install --no-adjust-repos {nodes}

This can be the default behavior by setting it in the right section in the
configuration file, which should look like this::

    [ceph-deploy-install]
    adjust_repos = False

The default for ``adjust_repos`` is ``True``, but because we are changing this
to ``False`` the CLI will now have this behavior changed without the need to
pass any flag.

Repository Sections
-------------------
Keys will depend on the type of package manager that will use it. Certain keys
for yum are required (like ``baseurl``) and some others like ``gpgcheck`` are
optional.

For both yum and apt these would be all the required keys in a repository section:

* baseurl
* gpgkey

If a required key is not present ceph-deploy will abort the installation
process with an error identifying the section and key what was missing.

In yum the repository name is taken from the section, so if the section is
``[foo]``, then the name of the repository will be ``foo repo`` and the
filename written to ``/etc/yum.repos.d/`` will be ``foo.repo``.

For apt, the same happens except the directory location changes to:
``/etc/apt/sources.list.d/`` and the file becomes ``foo.list``.


Optional values for yum
-----------------------
**name**:  A descriptive name for the repository. If not provided ``{repo
section} repo`` is used

**enabled**: Defaults to ``1``

**gpgcheck**: Defaults to ``1``

**type**: Defaults to ``rpm-md``

**gpgcheck**: Defaults to ``1``


Default Repository
------------------
For installations where a default repository is needed a key can be added to
that section to indicate it is the default one::

    [myrepo]
    default = true

When a default repository is detected it is mentioned in the log output and
ceph will get install from that one repository at the end.

Extra Repositories
------------------
If other repositories need to be installed aside from the main one, a key
should be added to represent that need with a comma separated value with the
name of the sections of the other repositories (just like the example
configuration file demonstrates)::

    [myrepo]
    baseurl = https://user:pass@example.org/rhel6
    gpgurl = https://example.org/keys/release.asc
    default = True
    extra-repos = cephrepo  # will install the cephrepo file too

    [cephrepo]
    name=ceph repo noarch packages
    baseurl=http://ceph.com/rpm-emperor/el6/noarch
    enabled=1
    gpgcheck=1
    type=rpm-md
    gpgkey=https://download.ceph.com/keys/release.asc

In this case, the repository called ``myrepo`` defines the ``extra-repos`` key
with just one extra one: ``cephrepo``.

This extra repository must exist as a section in the configuration file. After
the main one is added all the extra ones defined will follow. Installation of
Ceph will only happen with the main repository.
