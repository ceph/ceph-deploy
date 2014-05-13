

ceph_repo = """
[ceph]
name=Ceph packages for $basearch
baseurl={repo_url}/$basearch
enabled=1
gpgcheck=1
type=rpm-md
gpgkey={gpg_url}

[ceph-noarch]
name=Ceph noarch packages
baseurl={repo_url}/noarch
enabled=1
gpgcheck=1
type=rpm-md
gpgkey={gpg_url}

[ceph-source]
name=Ceph source packages
baseurl={repo_url}/SRPMS
enabled=0
gpgcheck=1
type=rpm-md
gpgkey={gpg_url}
"""

custom_repo = """
[{repo_name}]
name={name}
baseurl={baseurl}
enabled={enabled}
gpgcheck={gpgcheck}
type={_type}
gpgkey={gpgkey}
proxy={proxy}
"""
