#
# spec file for package ceph-deploy
#

%if 0%{?rhel} >= 8 || 0%{?suse_version} >= 1500
%bcond_with python2
%bcond_without python3
%else
%bcond_without python2
%bcond_with python3
%endif

# Exclude ceph-deploy from the rpmbuild shebang check to allow it to run
# under Python 2 and 3.
%global __brp_mangle_shebangs_exclude_from ceph-deploy

#################################################################################
# common
#################################################################################
Name:           ceph-deploy
Version:       2.1.0
Release:        0
Summary:        Admin and deploy tool for Ceph
License:        MIT
Group:          System/Filesystems
URL:            http://ceph.com/
Source0:        %{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%if %{with python2}
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
BuildRequires:  python2-virtualenv
BuildRequires:  python2-mock
BuildRequires:  python-tox
BuildRequires:  git
%if 0%{?suse_version}
BuildRequires:  python-pytest
%else
BuildRequires:  pytest
%endif
%endif
%if %{with python3}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-virtualenv
BuildRequires:  python%{python3_pkgversion}-mock
BuildRequires:  python%{python3_pkgversion}-tox
BuildRequires:  python%{python3_pkgversion}-pytest
%endif
BuildArch:      noarch
%description
An easy to use admin tool for deploy ceph storage clusters.


%if %{with python2}
%package -n python2-%{name}
Summary:        %{summary}
Requires:       python2-argparse
Requires:       python2-configparser
Requires:       python2-remoto
%{?python_provide:%python_provide python2-%{name}}
Provides:       ceph-deploy
%description -n python2-%{name}
An easy to use admin tool for deploy ceph storage clusters.
%endif

%if %{with python3}
%package -n python%{python3_pkgversion}-%{name}
Summary:        %{summary}
Requires:       python%{python3_pkgversion}-remoto
%{?python_provide:%python_provide python%{python3_pkgversion}-%{name}}
Conflicts:      ceph-deploy < 2.1.0
%description -n python%{python3_pkgversion}-%{name}
An easy to use admin tool for deploy ceph storage clusters.
%endif

#################################################################################
# specific
#################################################################################
%if 0%{defined suse_version}
%py_requires
%endif

%prep
#%%setup -q -n %%{name}
%setup -q

%build
# %{?with_python2:%py2_build}
# %{?with_python3:%py3_build}

%install
%if %{with python2}
%py2_install
mv %{buildroot}%{_bindir}/ceph-deploy %{buildroot}%{_bindir}/ceph-deploy-%{python2_version}
ln -s ./ceph-deploy-%{python2_version} %{buildroot}%{_bindir}/ceph-deploy-2
ln -s ./ceph-deploy-2 %{buildroot}%{_bindir}/ceph-deploy
%endif
%if %{with python3}
%py3_install
mv %{buildroot}%{_bindir}/ceph-deploy %{buildroot}%{_bindir}/ceph-deploy-%{python3_version}
ln -s ./ceph-deploy-%{python3_version} %{buildroot}%{_bindir}/ceph-deploy-3
%endif

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%if %{with python2}
%files -n python2-%{name}
%defattr(-,root,root)
%license LICENSE
%doc README.rst
%{python2_sitelib}/*
%{_bindir}/ceph-deploy
%{_bindir}/ceph-deploy-2
%{_bindir}/ceph-deploy-%{python2_version}
%endif

%if %{with python3}
%files -n python3-%{name}
%defattr(-,root,root)
%license LICENSE
%doc README.rst
%{python3_sitelib}/*
%{_bindir}/ceph-deploy-3
%{_bindir}/ceph-deploy-%{python3_version}
%endif

%changelog
