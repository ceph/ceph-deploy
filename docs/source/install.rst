
.. _install:

``install``
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

Before any action is taken, a platform detection call is done to make sure that
the platform that will get ceph installed is the correct one. If the platform
is not supported no further actions will proceed and an error message will be
displayed, similar to::

    [ceph_deploy][ERROR ] UnsupportedPlatform: Platform is not supported: Mandriva


.. _install-stable-releases

Stable releases
---------------
By default the *latest* stable release is assumed. This value changes when
newer versions are available. If you are automating deployments it is better to
specify exactly what release you need::

    ceph-deploy install --stable emperor {host}


.. _install-unstable-releases

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


.. _install-behind-firewall

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

.. _note::
    It is currently not possible to specify what version/release is to be
    installed when ``--repo-url`` is used.

It is strongly suggested that both flags be provided. However, the
``--gpg-url`` will default to the current one in the ceph repository::

    https://ceph.com/git/?p=ceph.git;a=blob_plain;f=keys/release.asc

.. versionadded:: 1.3.3
