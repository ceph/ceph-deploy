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


Creating a new cluster
======================

To create a new Ceph cluster, you need some servers. You should be
able to SSH to them without passwords (use SSH keys and an agent),
and you should have passwordless ``sudo`` set up on the servers.

To create a new configuration file, decide what hosts will run
``ceph-mon``, and run::

  ceph-deploy new MON [MON..]

listing the hostnames of the monitors.

The above will create a ``ceph.conf`` in your current directory. You
can edit ``ceph.conf`` it if you want.


Deploying monitors
==================

To actually deploy ``ceph-mon`` to the hosts you chose, run::

  ceph-deploy mon [HOST..]

Without explicit hosts listed, hosts in ``mon_initial_members`` in the
config file are deployed. That is, the hosts you passed to
``ceph-deploy new`` are the default value here.


Deploying OSDs
==============

To prepare a node for running OSDs, run::

  ceph-deploy osd HOST [HOST..]

After that, the hosts are able to run OSDs. To actually run OSDs, you
need to prepare data disks for that use.


Multiple clusters
=================

All of the above commands take a ``--cluster=NAME`` option, allowing
you to manage multiple clusters conveniently from one workstation.
For example::

  ceph-deploy --cluster=us-west new
  vi us-west.conf
  ceph-deploy --cluster=us-west mon
