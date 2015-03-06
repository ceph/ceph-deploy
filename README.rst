========================================================
 ceph-deploy -- Deploy Ceph with minimal infrastructure
========================================================

``ceph-deploy`` is a way to deploy Ceph relying on just SSH access to
the servers, ``sudo``, and some Python. It runs fully on your
workstation, requiring no servers, databases, or anything like that.

If you set up and tear down Ceph clusters a lot, and want minimal
extra bureaucracy, this is for you.

This ``README`` provides a brief overview of ceph-deploy, for thorough
documentation please go to http://ceph.com/ceph-deploy/docs

.. _what this tool is not:

What this tool is not
---------------------
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
All new releases of ``ceph-deploy`` are pushed to all ``ceph`` DEB release
repos.

The DEB release repos are found at::

     http://ceph.com/debian-{release}
     http://ceph.com/debian-testing

This means, for example, that installing ``ceph-deploy`` from
http://ceph.com/debian-giant will install the same version as from
http://ceph.com/debian-firefly or http://ceph.com/debian-testing.

RPM
---
All new releases of ``ceph-deploy`` are pushed to all ``ceph`` RPM release
repos.

The RPM release repos are found at::

     http://ceph.com/rpm-{release}
     http://ceph.com/rpm-testing

Make sure you add the proper one for your distribution (i.e. el7 vs rhel7).

This means, for example, that installing ``ceph-deploy`` from
http://ceph.com/rpm-giant will install the same version as from
http://ceph.com/rpm-firefly or http://ceph.com/rpm-testing.

bootstrapping
-------------
To get the source tree ready for use, run this once::

  ./bootstrap

You can symlink the ``ceph-deploy`` script in this somewhere
convenient (like ``~/bin``), or add the current directory to ``PATH``,
or just always type the full path to ``ceph-deploy``.


SSH and Remote Connections
==========================
``ceph-deploy`` will attempt to connect via SSH to hosts when the hostnames do
not match the current host's hostname. For example, if you are connecting to
host ``node1`` it will attempt an SSH connection as long as the current host's
hostname is *not* ``node1``.

ceph-deploy at a minimum requires that the machine from which the script is
being run can ssh as root without password into each Ceph node.

To enable this generate a new ssh keypair for the root user with no passphrase
and place the public key (``id_rsa.pub`` or ``id_dsa.pub``) in::

    /root/.ssh/authorized_keys

and ensure that the following lines are in the sshd config::

    PermitRootLogin without-password
    PubkeyAuthentication yes

The machine running ceph-deploy does not need to have the Ceph packages
installed unless it needs to admin the cluster directly using the ``ceph``
command line tool.


usernames
---------
When not specified the connection will be done with the same username as the
one executing ``ceph-deploy``. This is useful if the same username is shared in
all the nodes but can be cumbersome if that is not the case.

A way to avoid this is to define the correct usernames to connect with in the
SSH config, but you can also use the ``--username`` flag as well::

    ceph-deploy --username ceph install node1

``ceph-deploy`` then in turn would use ``ceph@node1`` to connect to that host.

This would be the same expectation for any action that warrants a connection to
a remote host.


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
(you already have one) and optionally skip installation and/or monitor
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
If attempting to install behind a firewall or through a proxy you can
use the ``--no-adjust-repos`` that will tell ceph-deploy to skip any changes
to the distro's repository in order to install the packages and it will go
straight to package installation.

That will allow an environment without internet access to point to *its own
repositories*. This means that those repositories will need to be properly
setup (and mirrored with all the necessary dependencies) before attempting an
install.

Another alternative is to set the ``wget`` env variables to point to the right
hosts, for example, put following lines into ``/root/.wgetrc`` on each node
(since ceph-deploy runs wget as root)::

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

FAQ
===

Before anything
---------------
Make sure you have the latest version of ``ceph-deploy``. It is actively
developed and releases are coming weekly (on average). The most recent versions
of ``ceph-deploy`` will have a ``--version`` flag you can use, otherwise check
with your package manager and update if there is anything new.

Why is feature X not implemented?
---------------------------------
Usually, features are added when/if it is sensible for someone that wants to
get started with ceph and said feature would make sense in that context.  If
you believe this is the case and you've read "`what this tool is not`_" and
still think feature ``X`` should exist in ceph-deploy, open a feature request
in the ceph tracker: http://tracker.ceph.com/projects/ceph-deploy/issues

A command gave me an error, what is going on?
---------------------------------------------
Most of the commands for ``ceph-deploy`` are meant to be run remotely in a host
that you have configured when creating the initial config. If a given command
is not working as expected try to run the command that failed in the remote
host and assert the behavior there.

If the behavior in the remote host is the same, then it is probably not
something wrong with ``ceph-deploy`` per-se. Make sure you capture the output
of both the ``ceph-deploy`` output and the output of the command in the remote
host.

Issues with monitors
--------------------
If your monitors are not starting, make sure that the ``{hostname}`` you used
when you ran ``ceph-deploy mon create {hostname}`` match the actual ``hostname -s``
in the remote host.

Newer versions of ``ceph-deploy`` should warn you if the results are different
but that might prevent the monitors from reaching quorum.

Developing ceph-deploy
======================
Now that you have cracked your teeth on Ceph, you might find that you want to
contribute to ceph-deploy.

Resources
---------
Bug tracking: http://tracker.ceph.com/projects/ceph-deploy/issues

Mailing list and IRC info is the same as ceph http://ceph.com/resources/mailing-list-irc/

Submitting Patches
------------------
Please add test cases to cover any code you add. You can test your changes
by running ``tox`` (You will also need ``mock`` and ``pytest`` ) from inside
the git clone

When creating a commit message please use ``git commit -s`` or otherwise add
``Signed-off-by: Your Name <email@address.dom>`` to your commit message.

Patches can then be submitted by a pull request on GitHub.
