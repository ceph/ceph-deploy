.. _mon:

mon
=======
The ``mon`` subcommand provides an interface to interact with a cluster's
monitors. The tool makes a few assumptions that are needed to implement the
most common scenarios. Monitors are usually very particular in what they need
to work correctly.

.. note:: Before version v1.5.33 ceph-deploy relied upon ``ceph-create-keys``.
          Using ``ceph-create-keys`` produced a side effect of deploying all
          bootstrap keys on the mon node so making all mon nodes admin nodes.
          This can be recreated by running the admin command on all mon nodes
          see :ref:`admin` section.

create-initial
------------------
Will deploy for monitors defined in ``mon initial members``, wait until
they form quorum and then ``gatherkeys``, reporting the monitor status along
the process. If monitors don't form quorum the command will eventually
time out.

This is the *preferred* way of initially deploying monitors since it will
compound a few of the steps needed together while looking for possible issues
along the way.

::

    ceph-deploy mon create-initial


create
----------
Deploy monitors by specifying directly like::

    ceph-deploy mon create node1 node2 node3

If no hosts are passed it will default to use the `mon initial members`
defined in the configuration.

Please note that if this is an initial monitor deployment, the preferred way
is to use ``create-initial``.


add
-------
Add a monitor to an existing cluster::

    ceph-deploy mon add node1

Since monitor hosts can have different network interfaces, this command allows
you to specify the interface IP in a few different ways.

**``--address``**: this will explicitly override any configured address for
that host. Usage::

    ceph-deploy mon add node1 --address 192.168.1.10


**ceph.conf**: If a section for the node that is being added exists and it
defines a ``mon addr`` key. For example::

    [mon.node1]
    mon addr = 192.168.1.10

**resolving/dns**: if the monitor address is not defined in the configuration file
nor overridden in the command-line it will fall-back to resolving the address
of the provided host.

.. warning:: If the monitor host has multiple addresses you should specify
             the address directly to ensure the right IP is used. Please
             note, only one node can be added at a time.

.. versionadded:: 1.4.0


destroy
-----------
Completely remove monitors on a remote host. Requires hostname(s) as
arguments::

    ceph-deploy mon destroy node1 node2 node3


--keyrings
--------------
Both ``create`` and ``create-initial`` subcommands can be used with the
``--keyrings`` flag that accepts a path to search for keyring files.

When this flag is used it will then look into the passed in path for files that
end with ``.keyring`` and will proceed to concatenate them in memory and seed
them to the monitor being created in the remote mode.

This is useful when having several different keyring files that are needed at
initial setup, but normally, ceph-deploy will only use the
``$cluster.mon.keyring`` file for initial seeding.

To keep things in order, create a directory and use that directory to store all
the keyring files that are needed. This is how the commands would look like for
a directory called ``keyrings``::

    ceph-deploy mon --keyrings keyrings create-initial

Or for the ``create`` sub-command::

    ceph-deploy mon --keyrings keyrings create {nodes}
