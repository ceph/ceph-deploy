========================================================
 ceph-deploy -- Deploy Ceph with minimal infrastructure
========================================================

``ceph-deploy`` is a way to deploy Ceph relying on just SSH access to
the servers, ``sudo``, and some Python. It runs fully on your
workstation, requiring no servers, databases, or anything like that.
It is not a generic deployment system, it is only for Ceph.

If you never wanted to install and learn Chef, Puppet or Juju, this is
for you.

If you set up and tear down Ceph clusters a lot, and want minimal
extra bureaucracy, this is for you.


Setup
=====

To get the source tree ready for use, run this once::

  ./bootstrap

You can symlink the ``ceph-deploy`` script in this somewhere
convenient (like ``~/bin``), or add the current directory to ``PATH``,
or just always type the full path to ``ceph-deploy``.


Managing an existing cluster
============================

You can use ceph-deploy to provision nodes for an existing cluster.
To grab a copy of the cluster configuration file (normally
``ceph.conf``)::

 ceph-deploy discover HOST

You will usually also want to gather the encryption keys used for that
cluster:

 ceph-deploy gatherkeys MONHOST

At this point you can skip the steps below that create a new cluster
(you already have one) and optionally skip instalation and/or monitor
creation, depending on what you are trying to accomplish.


Creating a new cluster
======================

Creating a new configuration
----------------------------

To create a new Ceph cluster, you need some servers. You should be
able to SSH to them without passwords (use SSH keys and an agent),
and you should have passwordless ``sudo`` set up on the servers.

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

The above will create a ``ceph.conf`` and ``ceph.mon.keyring'' in your
current directory.


Edit initial cluster configuration
----------------------------------

You want to review the generated ``ceph.conf`` file and make sure that
the ``mon_host`` setting contains the IP addresses you would like the
monitors to bind to.  These are the IPs that clients will initially
contact to authenticate to the cluster, and they need to be reachable
both by external client-facing hosts and internal cluster daemons.

Installing packages
===================

To install the Ceph software on the servers, run::

  ceph-deploy install HOST [HOST..]

This installs the current default *stable* release. You can choose a
different release track with command line options, for example to use
a release candidate::

  ceph-deploy install --testing HOST 

Or to test a development branch::

  ceph-deploy install --dev=wip-mds-now-works-no-kidding HOST [HOST..] 


Deploying monitors
==================

To actually deploy ``ceph-mon`` to the hosts you chose, run::

  ceph-deploy mon create HOST [HOST..]

Without explicit hosts listed, hosts in ``mon_initial_members`` in the
config file are deployed. That is, the hosts you passed to
``ceph-deploy new`` are the default value here.

Gather keys
===========

To gather authenticate keys (for administering the cluster and
bootstrapping new nodes) to the local directory, run::

  ceph-deploy gatherkeys HOST [HOST...]

where ``HOST'' is one of the monitor hosts.

Once these keys are in the local directory, you can provision new OSDs etc.


Deploying OSDs
==============

To prepare a node for running OSDs, run::

  ceph-deploy osd create HOST:DISK[:JOURNAL] [HOST:DISK[:JOURNAL] ...]

After that, the hosts will be running OSDs for the given data disks.
If you specify a raw disk (e.g., ``/dev/sdb``), partitions will be
created and GPT labels will be used to mark and automatically activate
OSD volumes.  If an existing partition is specified, the partition
table will not be modified.  If you want to destroy the existing
partition table on DISK first, you can include the ``--zap-disk``
option.

If there is already a prepared disk or directory that is ready to become an
OSD, you can also do:

 ceph-deploy osd activate HOST:DIR[:JOURNAL] [...]

This is useful when you are managing the mounting of volumes yourself.


Admin hosts
===========

To prepare a host with a ``ceph.conf`` and ``ceph.client.admin.keyring``
keyring so that it can administer the cluster, run::

  ceph-deploy admin HOST [HOST ...]

Forget keys
===========

The ``new`` and ``gatherkeys`` put some Ceph authentication keys in keyrings in
the local directory.  If you are worried about them being there for security
reasons, run::

  ceph-deploy forgetkeys

and they will be removed.  If you need them again later to deploy additional
nodes, simply re-run::

  ceph-deploy gatherkeys HOST [HOST...]

and they will be retrieved from an existing monitor node.

Multiple clusters
=================

All of the above commands take a ``--cluster=NAME`` option, allowing
you to manage multiple clusters conveniently from one workstation.
For example::

  ceph-deploy --cluster=us-west new
  vi us-west.conf
  ceph-deploy --cluster=us-west mon
