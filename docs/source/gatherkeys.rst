.. _gatherkeys:

==========
gatherkeys
==========

The ``gatherkeys`` subcommand provides an interface to get with a cluster's
cephx bootstrap keys.

keyrings
========
The ``gatherkeys`` subcommand retrieves the following keyrings.

ceph.mon.keyring
----------------
This keyring is used by all mon nodes to communicate with other mon nodes.

ceph.client.admin.keyring
-------------------------
This keyring is ceph client commands by default to administer the ceph cluster.

ceph.bootstrap-osd.keyring
--------------------------
This keyring is used to generate cephx keyrings for OSD instances.

ceph.bootstrap-mds.keyring
--------------------------
This keyring is used to generate cephx keyrings for MDS instances.

ceph.bootstrap-rgw.keyring
--------------------------
This keyring is used to generate cephx keyrings for RGW instances.

Example
=======
The ``gatherkeys`` subcommand contacts the mon and creates or retrieves existing
keyrings from the mon internal store. To run::

  ceph-deploy gatherkeys MON [MON..]

You can optionally add as many mon nodes to the command line as desired. The
``gatherkeys`` subcommand will succeed on the first mon to respond successfully
with all the keyrings.

Backing up of old keyrings
==========================

If old keyrings exist in the current working directory that do not match the
retrieved keyrings these old keyrings will be renamed with a time stamp
extention so you will not loose valuable keyrings.

.. note:: Before version v1.5.33 ceph-deploy relied upon ``ceph-create-keys``
          and did not backup existing keys. Using ``ceph-create-keys`` produced
          a side effect of deploying all bootstrap keys on the mon node so
          making all mon nodes admin nodes.
