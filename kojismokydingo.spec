# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


%global srcname kojismokydingo
%global srcver 2.2.0
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


# we don't generate binaries, let's turn that part off
%global debug_package %{nil}


# sure, we could build some docs
%bcond_with docs

%if %{with docs}
  %define ksd_docs %{_docdir}/%{srcname}
  %define __brp_mangle_shebangs_exclude_from \
          %{ksd_docs}/examples/script/whoami.py
%endif


%description
Koji Smoky Dingo


%prep
%setup -q


%build
%py3_build_wheel

%if %{with docs}
  %{python3} -B -m sphinx.cmd.build -b html docs build/sphinx/html
  %{python3} -B -m sphinx.cmd.build -b man docs build/sphinx/man
  %__rm -f build/sphinx/*/.buildinfo
%endif


%install
%__rm -rf $RPM_BUILD_ROOT

%py3_install_wheel %{srcname}-%{version}-py3-none-any.whl

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
BuildRequires:  python3-sphinx python3-sphinx-autodoc-typehints

%description -n %{srcname}-docs
Docs for Koji Smoky Dingo

%files -n %{srcname}-docs
%defattr(-,root,root,-)
%{_mandir}
%doc %{ksd_docs}

%endif


%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel
BuildRequires:  python3-pip python3-setuptools python3-wheel

Requires:	python3 python3-setuptools

%if 0%{?rhel} && 0%{?rhel} <= 8
# rhel/rocky 8 doesn't have the automatic Requires generation stuff,
# so we'll have to be explicit
Requires:       python3-appdirs
Requires:       python3-koji
Requires:       python3-typing-extensions
%endif

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


%changelog
* Mon Apr 01 2024 Christopher O'Brien <obriencj@gmail.com> - 2.2.0-0
- See the v2.2.0 release notes for a full list of changes

* Fri Mar 29 2024 Christopher O'Brien <obriencj@gmail.com> - 2.1.1-1
- Compatibility fixes for Koji 1.34.0
- See the v2.1.1 release notes for a full list of changes

* Fri Aug 11 2023 Christopher O'Brien <obriencj@gmail.com> - 2.1.0-1
- See the v2.1.0 release notes for a full list of changes

* Fri Jan 27 2023 Christopher O'Brien <obriencj@gmail.com> - 2.0.0-1
- Dropped RHEL 6, RHEL 7, and Python 2 support
- See the v2.0.0 release notes for a full list of changes

* Fri Oct 15 2021 Christopher O'Brien <obriencj@gmail.com> - 1.1.0-1
- See the v1.1.0 release notes for a full list of changes

* Thu Apr 1 2021 Christopher O'Brien <obriencj@gmail.com> - 1.0.0-1
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
