
%global srcname kojismokydingo
%global srcver 0.9.0


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


# There's two distinct eras of RPM packaging for python, with
# different macros and different expectations. Generally speaking the
# new features are available in RHEL 8+ and Fedora 22+

%define old_rhel ( 0%{?rhel} && 0%{?rhel} < 8 )
%define old_fedora ( 0%{?fedora} && 0%{?fedora} < 22 )

%if %{old_rhel} || %{old_fedora}
  %define old_python 1
%else
  %define old_python 0
  %bcond_with python2
  %bcond_without python3
%endif


# Some older koji fedora packages don't declare their python_provide
# even though the feature was available in the packaging macros. This
# means if we trying to rely on it, we'll produce a Requires for a
# python3.6dist(koji) and no package will ever provide it. Seems to be
# fixed from fedora 28 onwards.
%if ( 0%{?fedora} && 0%{?fedora} > 28 )
  %{?python_enable_dependency_generator}
%endif


%description
Koji Smoky Dingo


%prep
%setup -q


%build

%if %{old_python}
  # old python 2.6 support
  %{__python} setup.py build
  %{__python} setup-meta.py build

%else
  # newer python support, with optional settings for python2 and
  # python3

  %if %{with python2}
    %py2_build_wheel
    %{__python2} setup-meta.py bdist_wheel %{?py_setup_args}
  %endif

  %if %{with python3}
    %py3_build_wheel
    %{__python3} setup-meta.py bdist_wheel %{?py_setup_args}
  %endif

%endif


%install
rm -rf $RPM_BUILD_ROOT

%if %{old_python}
  %{__python} setup.py install --skip-build --root %{buildroot}
  %{__python} setup-meta.py install --skip-build --root %{buildroot}

%else
  %if %{with python2}
    %py2_install_wheel %{srcname}-%{version}-py2-none-any.whl
    %py2_install_wheel %{srcname}_meta-%{version}-py2-none-any.whl
  %endif

  %if %{with python3}
    %py3_install_wheel %{srcname}-%{version}-py3-none-any.whl
    %py3_install_wheel %{srcname}_meta-%{version}-py3-none-any.whl
  %endif

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

%if %{with python2}

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
%{python2_sitelib}/kojismokydingo
%{python2_sitelib}/kojismokydingo-%{version}.dist-info/


%package -n python2-%{srcname}-meta
Summary:        Koji Smoky Dingo Meta Plugin
BuildRequires:  python2-devel python2-setuptools
Requires:	python2 python2-setuptools python2-koji koji
%{?python_provide:%python_provide python2-%{srcname}-meta}

%description -n python2-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python2-%{srcname}-meta
%defattr(-,root,root,-)
%{python2_sitelib}/koji_cli_plugins/
%{python2_sitelib}/kojismokydingo_meta-*.dist-info/

%endif

%if %{with python3}

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel python3-setuptools python3-wheel python3-pip
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
BuildRequires:  python3-devel python3-setuptools
Requires:	python3 python3-setuptools python3-koji koji
%{?python_provide:%python_provide python3-%{srcname}-meta}

%description -n python3-%{srcname}-meta
Koji Smoky Dingo Meta Plugin

%files -n python3-%{srcname}-meta
%defattr(-,root,root,-)
%{python3_sitelib}/koji_cli_plugins/
%{python3_sitelib}/kojismokydingo_meta-*.dist-info/

%endif

%endif


%changelog
* Wed Jan 09 2019 Christopher O'Brien <obriencj@gmail.com> - 0.9.0-1
- Initial build.


# The end.
