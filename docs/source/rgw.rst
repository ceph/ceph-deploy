.. _rgw:

rgw
=======
The ``rgw`` subcommand provides an interface to interact with a cluster's
RADOS Gateway instances.

create
----------
Deploy RGW instances by specifying directly like::

    ceph-deploy rgw create node1 node2 node3

This will create an instance of RGW on the given node(s) and start the
corresponding service. The daemon will listen on the default port of 7480.

The RGW instances will default to having a name corresponding to the hostname
where it runs.  For example, ``rgw.node1``.

If a custom name is desired for the RGW daemon, it can be specific like::

    ceph-deploy rgw create node1:foo

Custom names are automatically prefixed with "rgw.", so the resulting daemon
name would be "rgw.foo".

.. note:: If an error is presented about the ``bootstrap-rgw`` keyring not being
          found, that is because the ``bootstrap-rgw`` only been auto-created on
          new clusters starting with the Hammer release.

.. versionadded:: 1.5.23

.. note:: Removing RGW instances is not yet supported

.. note:: Changing the port on which RGW will listen at deployment time is not yet
          supported.
