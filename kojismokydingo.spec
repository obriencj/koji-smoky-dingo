
%global srcname kojismokydingo
%global srcver 0.9.0


Summary: Koji Smoky Dingo
Name: %{srcname}
Version: %{srcver}
Release: 1%{?dist}
License: GPL v.3
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
%{__python2} setup-meta.py build %{?py_setup_args}
%{__python3} setup-meta.py build %{?py_setup_args}

%py2_build_wheel
%py3_build_wheel


%install
rm -rf $RPM_BUILD_ROOT

%{__python2} setup-meta.py install %{?py_setup_args}
%{__python3} setup-meta.py install %{?py_setup_args}

%py2_install_wheel %{srcname}-%{version}-py2-none-any.whl
%py3_install_wheel %{srcname}-%{version}-py3-none-any.whl


%clean
rm -rf $RPM_BUILD_ROOT


%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires:  python2-devel python2-setuptools python2-wheel python2-pip
Requires:	python2 python2-koji python2-six
Requires:	python2-%{srcname}-meta
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python2_sitelib}/kojismokydingo/
%{python2_sitelib}/kojismokydingo-%{version}.dist-info/


%package -n python2-%{srcname}-meta
Summary:        Koji Smoky Dingo Meta Plugin
BuildRequires:  python2-devel python2-setuptools
Requires:	python2 koji
%{?python_provide:%python_provide python2-%{srcname}-meta}

%description -n python2-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python2-%{srcname}-meta
%defattr(-,root,root,-)
%{python2_sitelib}/koji_cli_plugins/


%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel python3-wheel python3-pip
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
BuildRequires:  python3-devel
Requires:	python3 koji
%{?python_provide:%python_provide python3-%{srcname}-meta}

%description -n python3-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python3-%{srcname}-meta
%defattr(-,root,root,-)
%{python3_sitelib}/koji_cli_plugins/


%changelog
* Wed Jan 09 2019 Christopher O'Brien <obriencj@gmail.com> - 0.9.0-1
- Initial build.


# The end.
