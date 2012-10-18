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

If you edit the ``mon host`` entry in ``ceph.conf``, note that you
need to be able to SSH to those names or IP addresses too, and not
just the hostnames you use on the command line.

To create a new configuration file, decide what hosts will run
``ceph-mon``, and run::

  ceph-deploy new MON [MON..]

listing the hostnames of the monitors.

The above will create a ``ceph.conf`` in your current directory.

Edit initial cluster configuration
==================================

In particular, you should update the ``mon_host`` setting to list the
IP addresses you would like the monitors to bind to.  These are the
IPs that clients will initially contact to authenticate to the
cluster, and they need to be reachable both by external client-facing
hosts and internal cluster daemons.  In certain cases this setting can
be left as is (listing the monitor hostnames), but in most cases
``/etc/hosts`` files throw a wrench by mapping the hostname to
``127.0.1.1`` and preventing each node from reliably determining which
IP it should bind to.

Installing packages
===================

To install the Ceph software on the servers, run::

  ceph-deploy install HOST [HOST..]

This installs the current default *stable* release. You can choose a
different release track with command line options, for example to use
a release candidate::

  ceph-deploy install --testing myhost1

Or to test a development branch::

  ceph-deploy install --dev=wip-mds-now-works-no-kidding myhost1 myhost2


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

  ceph-deploy osd HOST:DISK [HOST:DISK..]

After that, the hosts will be running OSDs for the given data disks.


Multiple clusters
=================

All of the above commands take a ``--cluster=NAME`` option, allowing
you to manage multiple clusters conveniently from one workstation.
For example::

  ceph-deploy --cluster=us-west new
  vi us-west.conf
  ceph-deploy --cluster=us-west mon
