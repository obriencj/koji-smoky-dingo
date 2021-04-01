
%global srcname kojismokydingo
%global srcver 1.0.0
%global srcrel 1


Summary: Koji Smoky Dingo
Name: %{srcname}
Version: %{srcver}
Release: %{srcrel}%{?dist}
License: GPLv3
Group: Devel
URL: https://github.com/obriencj/koji-smoky-dingo
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch

Source0: %{name}-%{version}.tar.gz


# we don't generate binaries, let's turn that part off
%global debug_package %{nil}


# sure, we could build some docs
%bcond_with docs

%if %{with docs}
  %define ksd_docs %{_docdir}/%{srcname}
  %define __brp_mangle_shebangs_exclude_from \
          %{ksd_docs}/examples/script/whoami.py
%endif


# There's two distinct eras of RPM packaging for python, with
# different macros and different expectations. Generally speaking the
# new features are available in RHEL 8+ and Fedora 22+

%define old_rhel ( 0%{?rhel} && 0%{?rhel} < 8 )
%define old_fedora ( 0%{?fedora} && 0%{?fedora} < 22 )

%if %{old_rhel} || %{old_fedora}
  # old python 2.6 support
  %define with_old_python 1
  %undefine with_python2
  %undefine with_python3
%else
  # newer pythons, with cooler macros
  %undefine with_old_python
  %bcond_with python2
  %bcond_without python3
%endif


%description
Koji Smoky Dingo


%prep
%setup -q

%if %{with old_python}
  # this removes the deps on koji and appdirs from setup.py, because
  # on old environments they won't be available to the python dist
  # requirements generator
  patch -p1 < tools/missing_deps.patch
%endif


%build

%if %{with old_python}
  %{__python} setup.py build
%endif

%if %{with python2}
  %py2_build_wheel
%endif

%if %{with python3}
  %py3_build_wheel
%endif

%if %{with docs}
  %if %{with python3}
    %{python3} setup.py docs --builder html,man
  %else
    %{__python} setup.py docs --builder html,man
  %endif
  %__rm -f build/sphinx/html/.buildinfo
%endif


%install
%__rm -rf $RPM_BUILD_ROOT

%if %{with old_python}
  %{__python} setup.py install --skip-build --root %{buildroot}
%endif

%if %{with python2}
  %py2_install_wheel %{srcname}-%{version}-py2-none-any.whl
%endif

%if %{with python3}
  %py3_install_wheel %{srcname}-%{version}-py3-none-any.whl
%endif

%if %{with docs}

# we're going to manually copy these into place so that they land
# under /usr/share/doc/kojismokydingo rather than
# under /usr/share/doc/kojismokydingo-doc
%__mkdir_p %{buildroot}/%{ksd_docs}
%__cp -r examples %{buildroot}/%{ksd_docs}/examples
%__cp -r build/sphinx/html %{buildroot}/%{ksd_docs}/html

# our man pages
%__mkdir_p %{buildroot}/%{_mandir}/man7
%__cp build/sphinx/man/*.7 %{buildroot}/%{_mandir}/man7/
%endif


%clean
%__rm -rf $RPM_BUILD_ROOT


%if %{with docs}

%package -n %{srcname}-docs
Summary:        Documentation for %{srcname}
%if %{with python3}
BuildRequires:  make python3-sphinx
%else
BuildRequires:  make python2-sphinx
%endif

%description -n %{srcname}-docs
Docs for Koji Smoky Dingo

%files -n %{srcname}-docs
%defattr(-,root,root,-)
%{_mandir}
%doc %{ksd_docs}

%endif


%if %{with old_python}
# package support for older python systems (centos 6, fedora
# 19) with only python 2.6 available.

%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires:  python-devel python-setuptools
Requires:	python python-argparse python-setuptools python-six
Requires:       python2-koji
Obsoletes:	python2-%{srcname}-meta <= 0.9.0
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python_sitelib}/koji_cli_plugins/
%{python_sitelib}/kojismokydingo/
%{python_sitelib}/kojismokydingo-%{version}-py2.?.egg-info
%{_bindir}/ksd-filter-builds
%{_bindir}/ksd-filter-tags

%endif


%if %{with python2}

%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires:  python2-devel
BuildRequires:  python2-pip python2-setuptools python2-wheel
Requires:	python2 python2-appdirs python2-setuptools python2-six
Requires:       python2-koji
Obsoletes:	python2-%{srcname}-meta <= 0.9.0
%{?python_provide:%python_provide python2-%{srcname}}
%{?py_provides:%py_provides python2-%{srcname}}

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python2_sitelib}/koji_cli_plugins/
%{python2_sitelib}/kojismokydingo/
%{python2_sitelib}/kojismokydingo-%{version}.dist-info
%{_bindir}/ksd-filter-builds
%{_bindir}/ksd-filter-tags

%doc README.md
%license LICENSE

%endif


%if %{with python3}

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel
BuildRequires:  python3-pip python3-setuptools python3-wheel
Requires:	python3 python3-appdirs python3-setuptools python3-six
Requires:       python3-koji
Obsoletes:	python3-%{srcname}-meta <= 0.9.0
%{?python_provide:%python_provide python3-%{srcname}}
%{?py_provides:%py_provides python3-%{srcname}}

%description -n python3-%{srcname}
Koji Smoky Dingo

%files -n python3-%{srcname}
%defattr(-,root,root,-)
%{python3_sitelib}/koji_cli_plugins/
%{python3_sitelib}/kojismokydingo/
%{python3_sitelib}/kojismokydingo-%{version}.dist-info
%{_bindir}/ksd-filter-builds
%{_bindir}/ksd-filter-tags

%doc README.md
%license LICENSE

%endif


%changelog
* Thu Apr 1 2021 Christopher O'Brien <obriencj@gmail.com> - 1.0.0-0
- Finally at version 1.0.0!
- See the v1.0.0 release notes for a list of changes from the v0.9.7
  preview

* Wed Mar 10 2021 Christopher O'Brien <obriencj@gmail.com> - 0.9.7-1
- See the v0.9.7 release notes for a full list of changes

* Fri Jan 15 2021 Christopher O'Brien <obriencj@gmail.com> - 0.9.6-1
- See the v0.9.6 release notes for a full list of changes
- use a patch to disable koji as a setuptools requirement

* Fri Dec 18 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.5-1
- See the v0.9.5 release notes for a full list of changes
- remove install_requires for koji, because koji doesn't think it's a
  python package and in many cases this breaks things.

* Fri Dec 18 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.4-1
- See the v0.9.4 release notes for a full list of changes

* Fri Oct 02 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.3-1
- See the v0.9.3 release notes for a full list of changes

* Thu Sep 24 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.2-1
- See the v0.9.2 release notes for a full list of changes

* Fri Sep 18 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.1-1
- See the v0.9.1 release notes for a full list of changes
- Begin bumping micro for PRs as we work towards version 1.0.0
- All 0.9.z versions are still considered API unstable, this just helps
  to differentiate snapshots
- Moved to a single distribution containing both the python package
  and the koji meta-plugin

* Wed Jan 09 2019 Christopher O'Brien <obriencj@gmail.com> - 0.9.0-1
- See the v0.9.0 release notes for a list of initial features
- Initial build.


#
# The end.
