
%global srcname kojismokydingo
%global srcver 0.9.6
%global srcrel 0


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
Patch0: no-koji.patch


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
%patch0 -p1


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
BuildRequires:  python-setuptools
Requires:	python python-argparse python-setuptools python-six
Requires:       python2-koji
Obsoletes:	python2-%{srcname}-meta <= 0.9.0

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python_sitelib}/koji_cli_plugins/
%{python_sitelib}/kojismokydingo/
%{python_sitelib}/kojismokydingo-%{version}-py2.?.egg-info/
%{_bindir}/ksd-filter-builds
%{_bindir}/ksd-filter-tags

%endif


%if %{with python2}

%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires:  python2-devel python2-pip python2-setuptools python2-wheel
Requires:	python2 python2-setuptools python2-six
Requires:       python2-koji
Obsoletes:	python2-%{srcname}-meta <= 0.9.0
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
Koji Smoky Dingo

%files -n python2-%{srcname}
%defattr(-,root,root,-)
%{python2_sitelib}/koji_cli_plugins/
%{python2_sitelib}/kojismokydingo/
%{python2_sitelib}/kojismokydingo-%{version}.dist-info/
%{_bindir}/ksd-filter-builds
%{_bindir}/ksd-filter-tags

%doc README.md
%license LICENSE

%endif


%if %{with python3}

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel python3-pip python3-setuptools python3-wheel
Requires:	python3 python3-setuptools python3-six
Requires:       python3-koji
Obsoletes:	python3-%{srcname}-meta <= 0.9.0
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
Koji Smoky Dingo

%files -n python3-%{srcname}
%defattr(-,root,root,-)
%{python3_sitelib}/koji_cli_plugins/
%{python3_sitelib}/kojismokydingo/
%{python3_sitelib}/kojismokydingo-%{version}.dist-info/
%{_bindir}/ksd-filter-builds
%{_bindir}/ksd-filter-tags

%doc README.md
%license LICENSE

%endif


%changelog
* Fri Dec 19 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.6-0
- use a patch to disable koji as a setuptools requirement
- added build sieves 'compare-latest-nvr' and 'compare-latest-id'
- refactored sieve caching
- Added 'koji open' command which will launch a browser to the info
  page for the relevant koji data type.
- Added 'koji filter-tags' command and 'ksd-filter-tags' standalone
  command for applying sifty predicates to filter a list of tags

* Fri Dec 18 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.5-1
- remove install_requires for koji, because koji doesn't think it's a
  python package and in many cases this breaks things.
- fix issue with tags option in filter-builds

* Fri Dec 18 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.4-1
- list-build-archives now accepts multiple NVRs
- list-build-archives and latest-archives now accept '--arch=ARCH'
- moved as_userinfo to kojismokydingo package
- add int_or_str helper function to kojismokydingo.cli
- unique now accepts a 'key=' parameter to allow deduplication of
  otherwise unhashable values
- parse_datetime now accepts a 'strict=' parameter to let it return
  None instead of raising an Exception when parsing fails
- filtering expressions support added to list-component-builds and
  filter-builds commands
- ksd-filter-builds stand-alone command added to act as a shbang for
  reusable filtering scripts
- filter-builds and list-component-builds now accept multiple '--tag'
  options

* Fri Oct 02 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.3-1
- add iter_bulk_load generator function
- fix exception in kojismokyding.cli.tabulate for None values
- rename unset-env-var to remove-env-var
- rename unset-rpm-macro to remove-rpm-macro
- added block-env-var and block-rpm-macro (requires koji 1.23)
- added FeatureUnavailable exception type
- updated list-tag-extras to add a '--blocked' option
- add ensure_tag function
- updated bulk-tag-builds to add a '--create' option
- add version_check and version_require functions

* Thu Sep 24 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.2-1
- fix issue with 'set-rpm-macro --help'
- fix datetime issues in check-hosts
- add new parse_datetime function in common
- explicitly deactivate plugin command sessions 'SmokyDingo.deactivate'
- refactored how plugin commands populate parser arguments
- augmented the input logic for filter-builds, bulk-tag-builds, and
  list-component-builds to read from args or stdin as appropriate
- added state filtering to BuildFilter and to the filter-builds and
  list-component-builds commands
- fixed logic bug with bulk_load and related functions over error
  handling
- ManagedClientSession no longer loads configuration from a profile
- added ProfileClientSession
- refactored list-cgs and added cginfo

* Fri Sep 18 2020 Christopher O'Brien <obriencj@gmail.com> - 0.9.1-1
- Begin bumping micro for PRs as we work towards version 1.0.0
- All 0.9.z versions are still considered API unstable, this just helps
  to differentiate snapshots
- Moved to a single distribution containing including the package and
  the metaplugin
- added new filter-builds and list-component-builds commands
- removed list-imported (behavior now available in filter-builds)
- slightly beefed up docs
- moved as_buildinfo, as_taginfo, as_targetinfo into the main
  kojismokydingo package
- decorate_build_archive_data is now idempotent and slightly less
  expensive

* Wed Jan 09 2019 Christopher O'Brien <obriencj@gmail.com> - 0.9.0-1
- Initial build.


# The end.
