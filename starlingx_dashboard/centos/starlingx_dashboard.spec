##
Summary: stx horizon plugins
Name: starlingx_dashboard
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
install -p -D -m 755 starlingx_dashboard/enabled/* %{buildroot}%{enabled_dir}

%clean
echo "CLEAN CALLED"
rm -rf $RPM_BUILD_ROOT

%files
%{python2_sitelib}/%{name}

%{python2_sitelib}/%{name}-%{version}*.egg-info

%{enabled_dir}