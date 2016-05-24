.. _admin:

admin
=======
The ``admin`` subcommand provides an interface to add to the cluster's admin
node.

Example
-------
To make a node and admin node run::

  ceph-deploy admin ADMIN [ADMIN..]

This places the the cluster configuration and the admin keyring on the remote
nodes.

Admin node definition
---------------------

The definition of an admin node is that both the cluster configuration file
and the admin keyring. Both of these files are stored in the directory
/etc/ceph and thier prefix is that of the cluster name.

The default ceph cluster name is "ceph". So with a cluster with a default name
the admin keyring is named /etc/ceph/ceph.client.admin.keyring while cluster
configuration file is named /etc/ceph/ceph.conf.
