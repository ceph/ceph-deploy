Name: ceph-deploy
Summary: Ceph-deploy admin tool for Ceph
Version: 0.0.1
Release: 0
License: MIT
Group:   System Environment/Base
URL:     http://ceph.com/
#Source: %{name}-%{version}.tar.gz
Source: %{name}.tar.gz
BuildRoot: %{_tmppath}/%{name}-root
BuildArchitectures: noarch

%if 0%{?rhel}
BuildRequires: python >= %{pyver}
Requires: python >= %{pyver}
%endif
%if 0%{?suse_version}
BuildRequires: python >= %{pyver}
Requires: python >= %{pyver}
%endif

%description
Ceph-deploy is an easy to use admin tool for deploy
ceph storage clusters.

%prep

#%setup -q -n %{name}-%{version}
%setup -q -n %{name}

%build

%install

[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

python setup.py install --install-lib=/usr/share/ceph-deploy --root=$RPM_BUILD_ROOT
install -m 0755 -D scripts/ceph-deploy $RPM_BUILD_ROOT/usr/bin

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(-,root,root)
/usr/share/ceph-deploy/*
/usr/bin/ceph-deploy

%post

%preun

%changelog
* Mon Mar 10 2013 Gary Lowell <glowell@inktank.com>
- initial spec file
