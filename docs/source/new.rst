.. _new:

new
=======
This subcommand is used to generate a working ``ceph.conf`` file that will
contain important information for provisioning nodes and/or adding them to
a cluster.


SSH Keys
--------
Ideally, all nodes will be pre-configured to have their passwordless access
from the machine executing ``ceph-deploy`` but you can also take advantage of
automatic detection of this when calling the ``new`` subcommand.

Once called, it will try to establish an SSH connection to the hosts passed
into the ``new`` subcommand, and determine if it can (or cannot) connect
without a password prompt.

If it can't proceed, it will try to copy *existing* keys to the remote host, if
those do not exist, then passwordless ``rsa`` keys will be generated for the
current user and those will get used.

This feature can be overridden in the ``new`` subcommand like::

    ceph-deploy new --no-ssh-copykey

.. versionadded:: 1.3.2


Creating a new configuration
----------------------------

To create a new configuration file and secret key, decide what hosts
will run ``ceph-mon``, and run::

  ceph-deploy new MON [MON..]

listing the hostnames of the monitors.  Each ``MON`` can be

 * a simple hostname.  It must be DNS resolvable without the fully
   qualified domain name.
 * a fully qualified domain name.  The hostname is assumed to be the
   leading component up to the first ``.``.
 * a ``HOST:FQDN`` pair, of both the hostname and a fully qualified
   domain name or IP address.  For example, ``foo``,
   ``foo.example.com``, ``foo:something.example.com``, and
   ``foo:1.2.3.4`` are all valid.  Note, however, that the hostname
   should match that configured on the host ``foo``.

The above will create a ``ceph.conf`` and ``ceph.mon.keyring`` in your
current directory.


Edit initial cluster configuration
----------------------------------

You want to review the generated ``ceph.conf`` file and make sure that
the ``mon_host`` setting contains the IP addresses you would like the
monitors to bind to.  These are the IPs that clients will initially
contact to authenticate to the cluster, and they need to be reachable
both by external client-facing hosts and internal cluster daemons.


--cluster-network --public-network
----------------------------------
Are used to provide subnets so that nodes can communicate within that
network. If passed, validation will occur by looking at the remote IP addresses
and making sure that at least one of those addresses is valid for the given
subnet.

Those values will also be added to the generated ``ceph.conf``. If IPs are not
correct (or not in the subnets specified) an error will be raised.

.. versionadded:: 1.5.13
