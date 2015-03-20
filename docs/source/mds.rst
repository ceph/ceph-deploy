.. _mds:

mds
=======
The ``mds`` subcommand provides an interface to interact with a cluster's
CephFS Metadata servers.

create
----------
Deploy MDS instances by specifying directly like::

    ceph-deploy mds create node1 node2 node3

This will create an MDS on the given node(s) and start the
corresponding service.

The MDS instances will default to having a name corresponding to the hostname
where it runs.  For example, ``mds.node1``.

.. note:: Removing MDS instances is not yet supported
