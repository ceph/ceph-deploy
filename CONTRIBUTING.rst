Contributing to ceph-deploy
===========================
Before any contributions, a reference ticket *must* exist. The community issue
tracker is hosted at tracker.ceph.com

To open a new issue, requests can go to:

http://tracker.ceph.com/projects/ceph-deploy/issues/new


commits
-------
Once a ticket exists, commits should be prefaced by the ticket ID. This makes
it easier for maintainers to keep track of why a given line changed, mapping
directly to work done on a ticket.

For tickets coming from tracker.ceph.com, we expect the following format::

    [RM-0000] this is a commit message for tracker.ceph.com

``RM`` stands for Redmine which is the software running tracker.ceph.com.
Similarly, if a ticket was created in bugzilla.redhat.com, we expect the
following format::

    [BZ-0000] this is a commit message for bugzilla.redhat.com


To automate this process, you can create a branch with the tracker identifier
and id (replace "0000" with the ticket number)::

    git checkout -b RM-0000

And then use the follow prepare-commit-msg:
https://gist.github.com/alfredodeza/6d62d99a95c9a7975fbe

Copy that file to ``$GITREPOSITORY/.git/hooks/prepare-commit-msg``
and mark it executable.

Your commit messages should then be automatically prefixed with the branch name
based off of the issue tracker.

tests and documentation
-----------------------
Wherever it is feasible, tests must exist and documentation must be added or
improved depending on the change.

The build process not only runs tests but ensures that docs can be built from
the proposed changes as well.
