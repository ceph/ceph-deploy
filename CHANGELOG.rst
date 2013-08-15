
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
