1.5.1
-----
* Fixes a broken ``osd`` command that had the wrong attribute in the conn
  object

1.5.0
-----
* Warn if ``requiretty`` is causing issues
* Support IPV6 host resolution (Thanks Frode Nordahl)
* Fix incorrect paths for local cephdeploy.conf
* Support subcommand overrides defined in cephdeploy.conf
* When installing on CentOS/RHEL call ``yum clean all``
* Check OSD status when deploying to catch possible issues
* Add a ``--local-mirror`` flag for installation that syncs files
* Implement ``osd list`` to list remote osds
* Fix install issues on Suse (Thanks Owen Synge)

1.4.0
-----
* uninstall ceph-release and clean cache in CentOS
* Add ability to add monitors to an existing cluster
* Deprecate use of ``--stable`` for releases, introduce ``--release``
* Eat some tracebacks that may appear when closing remote connections
* Enable default ceph-deploy configurations for repo handling
* Fix wrong URL for rpm installs with ``--testing`` flag

1.3.5
-----
* Support Debian SID for installs
* Error nicely when hosts cannot be resolved
* Return a non-zero exit status when monitors have not formed quorum
* Use the new upstream library for remote connections (execnet 1.2)
* Ensure proper read permissions for ceph.conf when pushing configs
* clean up color logging for non-tty sessions
* do not reformat configs when pushing, pushes are now as-is
* remove dry-run flag that did nothing

1.3.4
-----
* ``/etc/ceph`` now gets completely removed when using ``purgedata``.
* Refuse to perform ``purgedata`` if ceph is installed
* Add more details when a given platform is not supported
* Use new Ceph auth settings for ``ceph.conf``
* Remove old journal size settings from ``ceph.conf``
* Add a new subcommand: ``pkg`` to install/remove packages from hosts


1.3.3
-----
* Add repo mirror support with ``--repo-url`` and ``--gpg-url``
* Remove dependency on the ``which`` command
* Fix problem when removing ``/var/lib/ceph`` and OSDs are still mounted
* Make sure all tmp files are closed before moving, fixes issue when creating
  keyrings and conf files
* Complete remove the lsb module


1.3.2
-----
* ``ceph-deploy new`` will now attempt to copy SSH keys if necessary unless it
  it disabled.
* Default to Emperor version of ceph when installing.

1.3.1
-----
* Use ``shutil.move`` to overwrite files from temporary ones (Thanks Mark
  Kirkwood)
* Fix failure to ``wget`` GPG keys on Debian and Debian-based distros when
  installing

1.3
---
* Major refactoring for all the remote connections in ceph-deploy. With global
  and granular timeouts.
* Raise the log level for missing keyrings
* Allow ``--username`` to be used for connecting over SSH
* Increase verbosity when MDS fails, include the exit code
* Do not remove ``/etc/ceph``, just the contents
* Use ``rcceph`` instead of service for SUSE
* Fix lack of ``--cluster`` usage on monitor error checks
* ensure we correctly detect Debian releases

1.2.7
-----
* Ensure local calls to ceph-deploy do not attempt to ssh.
* ``mon create-initial`` command to deploy all defined mons, wait for them to
  form quorum and finally to gatherkeys.
* Improve help menu for mon commands.
* Add ``--fs-type`` option to ``disk`` and ``osd`` commands (Thanks Benoit
  Knecht)
* Make sure we are using ``--cluster`` for remote configs when starting ceph
* Fix broken ``mon destroy`` calls using the new hostname resolution helper
* Add a helper to catch common monitor errors (reporting the status of a mon)
* Normalize all configuration options in ceph-deploy (Thanks Andrew Woodward)
* Use a ``cuttlefish`` compatible ``mon_status`` command
* Make ``osd activate`` use the new remote connection libraries for improved
  readability.
* Make ``disk zap`` also use the new remote connection libraries.
* Handle any connection errors that may came up when attempting to get into
  remote hosts.

1.2.6
-----
* Fixes a problem witha closed connection for Debian distros when creating
  a mon.

1.2.5
-----
* Fix yet another hanging problem when starting monitors. Closing the
  connection now before we even start them.

1.2.4
-----
* Improve ``osd help`` menu with path information
* Really discourage the use of ``ceph-deploy new [IP]``
* Fix hanging remote requests
* Add ``mon status`` output when creating monitors
* Fix Debian install issue (wrong parameter order) (Thanks Sayid Munawar)
* ``osd`` commands will be more verbose when deploying them
* Issue a warning when provided hosts do not match ``hostname -s`` remotely
* Create two flags for altering/not-altering source repos at install time:
  ``--adjust-repos`` and ``--no-adjust-repos``
* Do not do any ``sudo`` commands if user is root
* Use ``mon status`` for every ``mon`` deployment and detect problems with
  monitors.
* Allow to specify ``host:fqdn/ip`` for all mon commands (Thanks Dmitry
  Borodaenko)
* Be consistent for hostname detection (Thanks Dmitry Borodaenko)
* Fix hanging problem on remote hosts

1.2.3
-----
* Fix non-working ``disk list``
* ``check_call`` utility fixes ``$PATH`` issues.
* Use proper exit codes from the ``main()`` CLI function
* Do not error when attempting to add the EPEL repos.
* Do not complain when using IP:HOST pairs
* Report nicely when ``HOST:DISK`` is not used when zapping.

1.2.2
-----
* Do not force usage of lsb_release, fallback to
  ``platform.linux_distribution()``
* Ease installation in CentOS/Scientific by adding the EPEL repo
  before attempting to install Ceph.
* Graceful handling of pushy connection issues due to host
  address resolution
* Honor the usage of ``--cluster`` when calling osd prepare.

1.2.1
-----
* Print the help when no arguments are passed
* Add a ``--version`` flag
* Show the version in the help menu
* Catch ``DeployError`` exceptions nicely with the logger
* Fix blocked command when calling ``mon create``
* default to ``dumpling`` for installs
* halt execution on remote exceptions


1.2
---
* Better logging output
* Remote logging for individual actions for ``install`` and ``mon create``
* Install ``ca-certificates`` on all Debian-based distros
* Honor the usage of ``--cluster``
* Do not ``rm -rf`` monitor logs when destroying
* Error out when ``ceph-deploy new [IP]`` is used
* Log the ceph version when installing
