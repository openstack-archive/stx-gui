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
BuildRequires:  python2-pip
BuildRequires:  python2-wheel
Requires:       openstack-dashboard

BuildArch:      noarch

%description
starlingx specific horizon plugins

%define py_pkg_name          starlingx_dashboard
%define enabled_dir          %{_datadir}/openstack-dashboard/openstack_dashboard/enabled/
%define stx_themes_dir       %{_datadir}/openstack-dashboard/openstack_dashboard/themes/starlingx/
%define local_settings_dir   %{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d

%define debug_package %{nil}

%prep
%setup

%build
export PBR_VERSION=%{version}
%py2_build
%py2_build_wheel

%install
export PBR_VERSION=%{version}
%py2_install
mkdir -p $RPM_BUILD_ROOT/wheels
install -m 644 dist/*.whl $RPM_BUILD_ROOT/wheels/

install -d -m 755 %{buildroot}%{enabled_dir}
install -p -D -m 755 %{py_pkg_name}/enabled/* %{buildroot}%{enabled_dir}

install -d -m 755 %{buildroot}%{stx_themes_dir}
cp -R %{py_pkg_name}/themes/starlingx/* %{buildroot}%{stx_themes_dir}
chmod -R 755 %{buildroot}%{stx_themes_dir}/*

install -d -m 755 %{buildroot}%{local_settings_dir}
install -p -D -m 755 %{py_pkg_name}/local/local_settings.d/* %{buildroot}%{local_settings_dir}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{python2_sitelib}/%{py_pkg_name}

%{python2_sitelib}/%{py_pkg_name}-%{version}*.egg-info

%{enabled_dir}
%{stx_themes_dir}
%{local_settings_dir}

%package wheels
Summary: %{name} wheels

%description wheels
Contains python wheels for %{name}

%files wheels
/wheels/*
