#
# spec file for package ceph-deploy
#

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

#################################################################################
# common
#################################################################################
Name:		ceph-deploy
Version: 	1.2.3
Release: 	0
Summary: 	Admin and deploy tool for Ceph
License: 	MIT
Group:   	System/Filesystems
URL:     	http://ceph.com/
Source0: 	%{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  python-devel
BuildRequires:  python-distribute
BuildRequires:	python-setuptools
BuildRequires:	python-virtualenv
BuildRequires:  python-mock
BuildRequires:  python-tox
%if 0%{?suse_version}
BuildRequires:	python-pytest
%else
BuildRequires:	pytest
%endif
BuildRequires:  git
Requires:       python-argparse
Requires:       pushy >= 0.5.3
Requires:       python-distribute
#Requires:      lsb-release
#Requires:      ceph
%if 0%{?suse_version} && 0%{?suse_version} <= 1110
%{!?python_sitelib: %global python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%else
BuildArch:      noarch
%endif

#################################################################################
# specific
#################################################################################
%if 0%{defined suse_version}
%py_requires
%endif

%if 0%{?rhel}
BuildRequires: 	python >= %{pyver}
Requires: 	python >= %{pyver}
%endif

%description
An easy to use admin tool for deploy ceph storage clusters.

%prep
#%setup -q -n %{name}
%setup -q

%build
#python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}
install -m 0755 -D scripts/ceph-deploy $RPM_BUILD_ROOT/usr/bin

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(-,root,root)
%doc LICENSE README.rst 
%{_bindir}/ceph-deploy
%{python_sitelib}/*

%changelog
