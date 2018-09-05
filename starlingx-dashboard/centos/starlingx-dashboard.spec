##
Summary: stx horizon plugins
Name: starlingx-dashboard
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown
Source0: %{name}-%{version}.tar.gz

BuildRequires:  python-setuptools
BuildRequires:  python-pbr
Requires:       openstack-dashboard

BuildArch:      noarch

%description
starlingx specific horizon plugins

%define py_pkg_name          starlingx_dashboard
%define enabled_dir          %{_datadir}/openstack-dashboard/openstack_dashboard/enabled/

%define debug_package %{nil}

%prep
%setup

%build
export PBR_VERSION=%{version}
%py2_build

%install
export PBR_VERSION=%{version}
%py2_install

install -d -m 755 %{buildroot}%{enabled_dir}
install -p -D -m 755 %{py_pkg_name}/enabled/* %{buildroot}%{enabled_dir}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{python2_sitelib}/%{py_pkg_name}

%{python2_sitelib}/%{py_pkg_name}-%{version}*.egg-info

%{enabled_dir}