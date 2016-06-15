

ceph_repo = """[ceph]
name=Ceph packages for $basearch
baseurl={repo_url}/$basearch
enabled=1
gpgcheck={gpgcheck}
priority=1
type=rpm-md
gpgkey={gpg_url}

[ceph-noarch]
name=Ceph noarch packages
baseurl={repo_url}/noarch
enabled=1
gpgcheck={gpgcheck}
priority=1
type=rpm-md
gpgkey={gpg_url}

[ceph-source]
name=Ceph source packages
baseurl={repo_url}/SRPMS
enabled=0
gpgcheck={gpgcheck}
type=rpm-md
gpgkey={gpg_url}
"""

zypper_repo = """[ceph]
name=Ceph packages
type=rpm-md
baseurl={repo_url}
gpgcheck={gpgcheck}
gpgkey={gpg_url}
enabled=1
"""


def custom_repo(**kw):
    """
    Repo files need special care in that a whole line should not be present
    if there is no value for it. Because we were using `format()` we could
    not conditionally add a line for a repo file. So the end result would
    contain a key with a missing value (say if we were passing `None`).

    For example, it could look like::

        [ceph repo]
        name= ceph repo
        proxy=
        gpgcheck=

    Which breaks. This function allows us to conditionally add lines,
    preserving an order and be more careful.

    Previously, and for historical purposes, this is how the template used
    to look::

        custom_repo =
        [{repo_name}]
        name={name}
        baseurl={baseurl}
        enabled={enabled}
        gpgcheck={gpgcheck}
        type={_type}
        gpgkey={gpgkey}
        proxy={proxy}

    """
    lines = []

    # by using tuples (vs a dict) we preserve the order of what we want to
    # return, like starting with a [repo name]
    tmpl = (
        ('reponame', '[%s]'),
        ('name', 'name=%s'),
        ('baseurl', 'baseurl=%s'),
        ('enabled', 'enabled=%s'),
        ('gpgcheck', 'gpgcheck=%s'),
        ('_type', 'type=%s'),
        ('gpgkey', 'gpgkey=%s'),
        ('proxy', 'proxy=%s'),
        ('priority', 'priority=%s'),
    )

    for line in tmpl:
        tmpl_key, tmpl_value = line  # key values from tmpl

        # ensure that there is an actual value (not None nor empty string)
        if tmpl_key in kw and kw.get(tmpl_key) not in (None, ''):
            lines.append(tmpl_value % kw.get(tmpl_key))

    return '\n'.join(lines)
