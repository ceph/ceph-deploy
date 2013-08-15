========================================================
 ceph-deploy -- Deploy Ceph with minimal infrastructure
========================================================

``ceph-deploy`` is a way to deploy Ceph relying on just SSH access to
the servers, ``sudo``, and some Python. It runs fully on your
workstation, requiring no servers, databases, or anything like that.

If you set up and tear down Ceph clusters a lot, and want minimal
extra bureaucracy, this is for you.

It is not a generic deployment system, it is only for Ceph, and is designed
for users who want to quickly get Ceph running with sensible initial settings
without the overhead of installing Chef, Puppet or Juju.

It does not handle client configuration beyond pushing the Ceph config file
and users who want fine-control over security settings, partitions or directory
locations should use a tool such as Chef or Puppet.

Installation
============
Depending on what type of usage you are going to have with ``ceph-deploy`` you
might want to look into the different ways to install it. For automation, you
might want to ``bootstrap`` directly. Regular users of ``ceph-deploy`` would
probably install from the OS packages or from the Python Package Index.

Python Package Index
--------------------
If you are familiar with Python install tools (like ``pip`` and
``easy_install``) you can easily install ``ceph-deploy`` like::

    pip install ceph-deploy

or::

    easy_install ceph-deploy


It should grab all the dependencies for you and install into the current user's
environment.

We highly recommend using ``virtualenv`` and installing dependencies in
a contained way.


DEB
---
The DEB repo can be found at http://ceph.com/packages/ceph-extras/debian/

But they can also be found for ``ceph`` releases in the ``ceph`` repos like::

     ceph.com/debian-{release}
     ceph.com/debian-testing

RPM
---
The RPM repos can be found at http://ceph.com/packages/ceph-extras/rpm/

Make sure you add the proper one for your distribution.

But they can also be found for ``ceph`` releases in the ``ceph`` repos like::

     ceph.com/rpm-{release}
     ceph.com/rpm-testing


bootstraping
------------
To get the source tree ready for use, run this once::

  ./bootstrap

You can symlink the ``ceph-deploy`` script in this somewhere
convenient (like ``~/bin``), or add the current directory to ``PATH``,
or just always type the full path to ``ceph-deploy``.

ceph-deploy at a minimum requires that the machine from which the script is
being run can ssh as root without password into each Ceph node.

To enable this generate a new ssh keypair for the root user with no passphrase
and place the public key (``id_rsa.pub`` or ``id_dsa.pub``) in::

    /root/.ssh/authorized_keys

and ensure that the following lines are in the sshd config::

    PermitRootLogin yes
    PermitEmptyPasswords yes

The machine running ceph-deploy does not need to have the Ceph packages installed
unless it needs to admin the cluster directly using the ``ceph`` command line tool.

Managing an existing cluster
============================

You can use ceph-deploy to provision nodes for an existing cluster.
To grab a copy of the cluster configuration file (normally
``ceph.conf``)::

 ceph-deploy config pull HOST

You will usually also want to gather the encryption keys used for that
cluster::

    ceph-deploy gatherkeys MONHOST

At this point you can skip the steps below that create a new cluster
(you already have one) and optionally skip instalation and/or monitor
creation, depending on what you are trying to accomplish.


Creating a new cluster
======================

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


Proxy or Firewall Installs
--------------------------
If attempting to install behind a firewall or through a proxy you will need to
set the `wget` env variables to point to the right hosts, for example::

    http_proxy=http://host:port
    ftp_proxy=http://host:port
    https_proxy=http://host:port


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

where ``HOST`` is one of the monitor hosts.

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
OSD, you can also do::

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
