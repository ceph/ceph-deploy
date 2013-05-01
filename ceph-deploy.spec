#
# spec file for package ceph-deploy
#

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%define builddir ./rpmbuild

#
# it seems that rpmbuild expands all these definitions twice during 
# a -bp run at least; I don't know why.  %global makes no difference,
# nor does %{expand}.
#

# this macro exists only for its side-effects. 
%define source_buildtar %{expand:%(%{__python} setup.py clean -a >/dev/null; %{__python} setup.py sdist --formats=bztar --dist-dir=%{builddir}/SOURCES >/dev/null)}
# apparently expand doesn't force evaluation.  Attempt to force with use
%{echo:%{source_buildtar}}

%define gitdesc %{expand:%(git describe --always)}
%define gitver %{expand:%(echo %{gitdesc} | sed 's/^v//')}
%define myver %{expand:%(echo %{gitver} | sed -e 's/-.*//')}
%define myrel %{expand:%(echo %{gitver} | sed -e s/%{myver}-// -e 's/-/./')}

#################################################################################
# common
#################################################################################
Name:		ceph-deploy
Version: 	%{myver}
Release: 	%{myrel}
Summary: 	Admin and deploy tool for Ceph
License: 	MIT
Group:   	System/Filesystems
URL:     	http://ceph.com/
Source0: 	%{name}-%{gitver}.tar.bz2
#Source0: 	https://github.com/ceph/ceph-deploy/archive/v0.1.tar.gz
#BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  python-devel
BuildRequires:  python-distribute
BuildRequires:	python-setuptools
BuildRequires:	python-virtualenv
BuildRequires:	pytest
BuildRequires:  python-mock
BuildRequires:  python-tox
Requires:       python-argparse
#Requires:	python-pushy
Requires:       python-distribute
#Requires:	lsb-release
Requires:	ceph
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
%if 0%{?suse_version} > 1210
Requires:       gptfdisk
%else
Requires:       scsirastools
%endif
%else
Requires:       gdisk
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
CEPH_DEPLOY_VERSION_FOR_PYTHON=%{gitver} python setup.py install --prefix=%{_prefix} --root=%{buildroot}
install -m 0755 -D scripts/ceph-deploy $RPM_BUILD_ROOT/usr/bin

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(-,root,root)
%doc LICENSE README.rst 
%{_bindir}/ceph-deploy
%{python_sitelib}/*

%changelog
