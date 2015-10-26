.. _repo:

repo
=====
Provides a simple interface for installing or removing new Apt or RPM repo files.

Apt repo files are added in ``/etc/apt/sources.list.d``, while RPM repo files
are added in ``/etc/yum.repos.d``.

.. _repo-install:

Installing repos
----------------

Repos can be defined through CLI arguments, or they can be defined in cephdeploy.conf
and referenced by name.

The general format for adding a repo is::

    ceph-deploy repo --repo-url <repo_url> --gpg-url <optional URL to GPG key> <repo-name> <host> [host [host ...]]

As an example of adding the Ceph rpm-hammer repo for EL7::

    ceph-deploy repo --repo-url http://ceph.com/rpm-hammer/el7/x86_64/ --gpg-url 'https://download.ceph.com/keys/release.asc' ceph HOST1

In this example, the repo-name is ``ceph``, and the file ``/etc/yum.repos.d/ceph.repo``
will be created. Because ``--gpg-url`` was passed, the repo will have ``gpgcheck=1``
and will reference the given GPG key.  

For APT, the equivalent example would be::

    ceph-deploy repo --repo-url http://ceph.com/debian-hammer --gpg-url 'https://download.ceph.com/keys/release.asc' ceph HOST1

If a repo was defined in cephdeploy.conf, like the following::

    [ceph-mon]
    name=Ceph-MON
    baseurl=https://cephmirror.com/hammer/el7/x86_64
    gpgkey=https://cephmirror.com/release.asc
    gpgcheck=1
    proxy=_none_

This could be installed with this command::

    ceph-deploy repo ceph-mon HOST1

``ceph-deploy repo`` will always check to see if a matching repo name exists in
cephdeploy.conf first.

It is possible that repos may be password protected, and a URL may be structured like so::

    https://<user>:<password>@host.com/...

In this case, Apt repositories will be created with mode ``0600`` to make
sure the password is not world-readable.  You can also use the
``CEPH_DEPLOY_REPO_URL`` and ``CEPH_DEPLOY_GPG_URL`` environment variables in lieu
of ``--repo-url`` and ``--gpg-url`` to avoid placing sensitive credentials on the
command line (and thus visible in the process table).

.. note::
    The writing of a repo file as mode 0600 when a password is present is only done
    for Apt repos currently.

.. _repo-remove:

Removing
--------

Repos are simply removed by name.  The general format for adding a repo is::

    ceph-deploy repo --remove <repo-name> <host> [host [host...]]

To remove a repo at ``/etc/yum.repos.d/ceph.repo``, do::

    ceph-deploy repo --remove ceph HOST1

.. versionadded:: 1.5.27
