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



