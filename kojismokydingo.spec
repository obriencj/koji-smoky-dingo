
%global srcname kojismokydingo
%global srcver 0.9.0


%if 0%{?rhel} < 7 || 0%{?fedora} < 19
%define old_python 1
%else
%define old_python 0
%endif


Summary: Koji Smoky Dingo
Name: %{srcname}
Version: %{srcver}
Release: 1%{?dist}
License: GPLv3
Group: Devel
URL: https://github.com/obriencj/koji-smoky-dingo
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildArch: noarch

%{?python_enable_dependency_generator}


%description
Koji Smoky Dingo


%prep
%setup -q


%build

%if %{old_python}
%{__python} setup.py build
%{__python} setup-meta.py build

%else
%py2_build_wheel
%py3_build_wheel
%{python2} setup-meta.py build %{?py_setup_args}
%{python3} setup-meta.py build %{?py_setup_args}
%endif


%install
rm -rf $RPM_BUILD_ROOT

%if %{old_python}
%{__python} setup.py install --skip-build --root %{buildroot}
%{__python} setup-meta.py install --skip-build --root %{buildroot}

%else
%py2_install_wheel %{srcname}-%{version}-py2-none-any.whl
%py3_install_wheel %{srcname}-%{version}-py3-none-any.whl
%{python2} setup-meta.py install --skip-build --root %{buildroot}
%{python3} setup-meta.py install --skip-build --root %{buildroot}
%endif


%clean
rm -rf $RPM_BUILD_ROOT


%if %{old_python}
# package support for older python systems (centos 6, fedora
# 19) with only python 2.6 available.


%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires:  python-setuptools
Requires:	python python-argparse python-six python2-koji
Requires:	python2-%{srcname}-meta

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python_sitelib}/kojismokydingo/
%{python_sitelib}/kojismokydingo-*.egg-info/


%package -n python2-%{srcname}-meta
Summary:        Koji Smoky Dingo Meta Plugin
BuildRequires:  python-setuptools
Requires:	koji python python-setuptools

%description -n python2-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python2-%{srcname}-meta
%defattr(-,root,root,-)
%{python_sitelib}/koji_cli_plugins/kojismokydingometa.*
%{python_sitelib}/kojismokydingo_meta-*.egg-info/


%else
# package support for more modern python2 & python3 environments

%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires:  python2-setuptools python2-wheel python2-pip
Requires:	python2 python2-koji python2-six
Requires:	python2-%{srcname}-meta
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python2_sitelib}/kojismokydingo
%{python2_sitelib}/kojismokydingo-%{version}.dist-info/


%package -n python2-%{srcname}-meta
Summary:        Koji Smoky Dingo Meta Plugin
BuildRequires:  python2-setuptools
Requires:	python2 python2-setuptools python2-koji
%{?python_provide:%python_provide python2-%{srcname}-meta}

%description -n python2-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python2-%{srcname}-meta
%defattr(-,root,root,-)
%{python2_sitelib}/koji_cli_plugins/kojismokydingometa.*
%{python2_sitelib}/kojismokydingo_meta-*.dist-info/


%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-setuptools python3-wheel python3-pip
Requires:	python3 python3-koji python3-six
Requires:	python3-%{srcname}-meta
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
Koji Smoky Dingo

%files -n python3-%{srcname}
%defattr(-,root,root,-)
%{python3_sitelib}/kojismokydingo/
%{python3_sitelib}/kojismokydingo-%{version}.dist-info/


%package -n python3-%{srcname}-meta
Summary:        Koji Smoky Dingo Meta Plugin
BuildRequires:  python3-setuptools
Requires:	python3 python3-setuptools python3-koji
%{?python_provide:%python_provide python3-%{srcname}-meta}

%description -n python3-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python3-%{srcname}-meta
%defattr(-,root,root,-)
%{python3_sitelib}/koji_cli_plugins/kojismokydingometa.*
%{python3_sitelib}/kojismokydingo_meta-*.dist-info/


%endif


%changelog
* Wed Jan 09 2019 Christopher O'Brien <obriencj@gmail.com> - 0.9.0-1
- Initial build.


# The end.
