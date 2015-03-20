
.. _pkg:

pkg
=======
Provides a simple interface to install or remove packages on a remote host (or
a number of remote hosts).

Packages to install or remove *must* be comma separated when there are more
than one package in the argument.

.. note::
    This feature only supports installing on same distributions. You cannot
    install a given package on different distributions at the same time.


.. _pkg-install:

--install
-------------
This flag will use the package (or packages) passed in to perform an installation using
the distribution package manager in a non-interactive way. Package managers
that tend to ask for confirmation will not prompt.

An example call to install a few packages on 2 hosts (with hostnames like
``node1`` and ``node2``) would look like::

    ceph-deploy pkg --install vim,zsh node1 node2
    [ceph_deploy.cli][INFO  ] Invoked (1.3.3): /bin/ceph-deploy pkg --install vim,zsh node1 node2
    [node1][DEBUG ] connected to host: node1
    [node1][DEBUG ] detect platform information from remote host
    [node1][DEBUG ] detect machine type
    [ceph_deploy.pkg][INFO  ] Distro info: Ubuntu 12.04 precise
    [node1][INFO  ] installing packages on node1
    [node1][INFO  ] Running command: sudo env DEBIAN_FRONTEND=noninteractive apt-get -q install --assume-yes vim zsh
    ...


.. _pkg-remove:

--remove
------------
This flag will use the package (or packages) passed in to remove them using
the distribution package manager in a non-interactive way. Package managers
that tend to ask for confirmation will not prompt.

An example call to remove a few packages on 2 hosts (with hostnames like
``node1`` and ``node2``) would look like::


    [ceph_deploy.cli][INFO  ] Invoked (1.3.3): /bin/ceph-deploy pkg --remove vim,zsh node1 node2
    [node1][DEBUG ] connected to host: node1
    [node1][DEBUG ] detect platform information from remote host
    [node1][DEBUG ] detect machine type
    [ceph_deploy.pkg][INFO  ] Distro info: Ubuntu 12.04 precise
    [node1][INFO  ] removing packages from node1
    [node1][INFO  ] Running command: sudo apt-get -q remove -f -y --force-yes -- vim zsh
    ...
