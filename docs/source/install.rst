
.. _install:

install
===========
A few different distributions are supported with some flags to allow some
customization for installing ceph on remote nodes.

Supported distributions:

* Ubuntu
* Debian
* Fedora
* RedHat
* CentOS
* Suse
* Scientific Linux
* Arch Linux

Before any action is taken, a platform detection call is done to make sure that
the platform that will get ceph installed is the correct one. If the platform
is not supported no further actions will proceed and an error message will be
displayed, similar to::

    [ceph_deploy][ERROR ] UnsupportedPlatform: Platform is not supported: Mandriva


.. _install-stable-releases:


.. _note:
    Although ceph-deploy installs some extra dependencies, do note that those
    are not going to be uninstalled. For example librbd1 and librados which
    qemu-kvm depends on, and removing it would cause issues for qemu-kvm.

Distribution Notes
------------------

RPMs
^^^^
On RPM-based distributions, ``yum-plugin-priorities`` is installed to make sure
that upstream ceph.com repos have a higher priority than distro repos.

Because of packaging splits that are present in downstream repos that may not
be present in ceph.com repos, ``ceph-deploy`` enables the ``check_obsoletes``
flag for the Yum priorities plugin.

.. versionchanged:: 1.5.22
   Enable ``check_obsoletes`` by default

RHEL
^^^^
When installing packages on systems running Red Hat Enterprise Linux (RHEL),
``ceph-deploy`` will not install the latest upstream release by default. On other
distros, running ``ceph-deploy install`` without the ``--release`` flag will
install the latest upstream release by default (i.e. firefly, giant, etc). On
RHEL, the ``--release`` flag *must* be used if you wish to use the upstream
packages hosted on http://ceph.com.

.. versionchanged:: 1.5.22
   Require ``--release`` flag to get upstream packages on RHEL

Specific Releases
-----------------
By default the *latest* release is assumed. This value changes when
newer versions are available. If you are automating deployments it is better to
specify exactly what release you need::

    ceph-deploy install --release emperor {host}


Note that the ``--stable`` flag for specifying a Ceph release is deprecated and
should no longer be used starting from version 1.3.6.

.. versionadded:: 1.4.0

.. _install-unstable-releases:

Unstable releases
-----------------
If you need to test cutting edge releases or a specific feature of ceph that
has yet to make it to a stable release you can specify this as well with
ceph-deploy with a couple of flags.

To get the latest development release::

    ceph-deploy install --testing {host}

For a far more granular approach, you may want to specify a branch or a tag
from the repository, if none specified it fall backs to the latest commit in
master::

    ceph-deploy install --dev {branch or tag} {host}


.. _install-behind-firewall:

Behind Firewall
---------------
For restrictive environments there are a couple of options to be able to
install ceph.

If hosts have had some customizations with custom repositories and all is
needed is to proceed with a install of ceph, we can skip altering the source
repositories like::

    ceph-deploy install --no-adjust-repos {host}

Note that you will need to have working repositories that have all the
dependencies that ceph needs. In some distributions, other repos (besides the
ceph repos) will be added, like EPEL for CentOS.

However, if there is a ceph repo mirror already set up you can point to it
before installation proceeds. For this specific action you will need two
arguments passed in (or optionally use environment variables).

The repository URL and the GPG URL can be specified like this::

    ceph-deploy install --repo-url {http mirror} --gpg-url {http gpg url} {host}

Optionally, you can use the following environment variables:

* ``CEPH_DEPLOY_REPO_URL``
* ``CEPH_DEPLOY_GPG_URL``

Those values will be used to write to the ceph ``sources.list`` (in Debian and
Debian-based distros) or the ``yum.repos`` file for RPM distros and will skip
trying to compose the right URL for the release being installed.

.. note::
    It is currently not possible to specify what version/release is to be
    installed when ``--repo-url`` is used.

It is strongly suggested that both flags be provided. However, the
``--gpg-url`` will default to the current one in the ceph repository::

    https://download.ceph.com/keys/release.asc

.. versionadded:: 1.3.3


Local Mirrors
-------------
``ceph-deploy`` supports local mirror installation by syncing a repository to
remote servers and configuring correctly the remote hosts to install directly
from those local paths (as opposed to going through the network).

The one requirement for this option to work is to have a ``release.asc`` at the
top of the directory that holds the repository files.

That file is used by Ceph as the key for its signed packages and it is usually
retrieved from::

        https://download.ceph.com/keys/release.asc

This is how it would look the process to get Ceph installed from a local
repository in an admin host::

    $ ceph-deploy install --local-mirror ~/tmp/rpm-mirror/ceph.com/rpm-emperor/el6 node2
    [ceph_deploy.cli][INFO  ] Invoked (1.4.1): /bin/ceph-deploy install --local-mirror /Users/alfredo/tmp/rpm-mirror/ceph.com/rpm-emperor/el6 node2
    [ceph_deploy.install][DEBUG ] Installing stable version emperor on cluster ceph hosts node2
    [ceph_deploy.install][DEBUG ] Detecting platform for host node2 ...
    [node2][DEBUG ] connected to host: node2
    [node2][DEBUG ] detect platform information from remote host
    [node2][DEBUG ] detect machine type
    [ceph_deploy.install][INFO  ] Distro info: CentOS 6.4 Final
    [node2][INFO  ] installing ceph on node2
    [node2][INFO  ] syncing file: noarch/ceph-deploy-1.3-0.noarch.rpm
    [node2][INFO  ] syncing file: noarch/ceph-deploy-1.3.1-0.noarch.rpm
    [node2][INFO  ] syncing file: noarch/ceph-deploy-1.3.2-0.noarch.rpm
    [node2][INFO  ] syncing file: noarch/ceph-release-1-0.el6.noarch.rpm
    [node2][INFO  ] syncing file: noarch/index.html
    [node2][INFO  ] syncing file: noarch/index.html?C=D;O=A
    [node2][INFO  ] syncing file: noarch/index.html?C=D;O=D
    [node2][INFO  ] syncing file: noarch/index.html?C=M;O=A
    ...
    [node2][DEBUG ]
    [node2][DEBUG ] Installed:
    [node2][DEBUG ]   ceph.x86_64 0:0.72.1-0.el6
    [node2][DEBUG ]
    [node2][DEBUG ] Complete!
    [node2][INFO  ] Running command: sudo ceph --version
    [node2][DEBUG ] ceph version 0.72.1
    (4d923861868f6a15dcb33fef7f50f674997322de)

.. versionadded:: 1.5.0


Repo file only
--------------
The ``install`` command has a flag that offers flexibility for installing
"repo files" only, avoiding installation of ceph and its dependencies.

These "repo files" are the configuration files for package managers ("yum" or
"apt" for example) that point to the right repository information so that
certain packages become available.

For APT  these files would be `list files` and for YUM they would be `repo
files`. Regardless of the package manager, ceph-deploy is able to install this
file correctly so that the Ceph packages are available. This is useful in
a situation where a massive upgrade is needed and ``ceph-deploy`` would be too
slow to install sequentially in every host.

Repositories are specified in the ``cephdeploy.conf`` (or
``$HOME/.cephdeploy.conf``) file. If a specific repository section is needed,
it can be specified with the ``--release`` flag::

    ceph-deploy install --repo --release firefly {HOSTS}

The above command would install the ``firefly`` repo file in every ``{HOST}``
specified.

If a repository section exists with the ``default = True`` flag, there is no
need to specify anything else and the repo file can be installed simply by
passing in the hosts::

    ceph-deploy install --repo {HOSTS}

.. versionadded:: 1.5.10
