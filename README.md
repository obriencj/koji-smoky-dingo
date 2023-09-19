# Overview

Koji Smoky Dingo is a collection of client command-line plugins for
the [Koji] build system, and a set of utility modules for writing your
own commands or scripts.

[koji]: https://pagure.io/koji

The phrase "smoky-dingo" was provided by [coolname] and has no
particular relevance.

[coolname]: https://pypi.org/project/coolname/


## Meta Plugin

This project provides a relatively tiny CLI plugin for koji, named
kojismokydingometa. The meta plugin acts as an adapter between koji's
existing CLI plugin loading framework and Python entry_points.

The meta plugin can be used to load additional commands beyond those
provided as part of this project. Simply register your commands with
the `"koji_smoky_dingo"` entry point key. See the [example command]
as a reference.

[example command]: https://github.com/obriencj/koji-smoky-dingo/blob/master/examples/command/


## Tag Commands

These commands modify tag features, requiring either the tag
permission (koji >= [1.18]) or the admin permission.

| Command | Description |
|---------|-------------|
|`block-env-var` |Blocks a mock environment variable from a tag. |
|`block-rpm-macro` |Blocks a mock RPM macro from a tag. |
|`bulk—move-builds` |Move a large amount of builds, bypassing the creation of individual tasks. |
|`bulk—tag-builds` |Tag a large amount of builds, bypassing the creation of individual tasks. |
|`bulk—untag-builds` |Untag a large amount of builds, bypassing the creation of individual tasks. |
|`remove-env-var` |Removes a mock environment variable from a tag. |
|`remove-rpm-macro` |Removes a mock RPM macro from a tag. |
|`renum—tag-inheritance` |Adjust the priority values of a tag to maintain the same inheritance order, but to create an even amount of space between each entry. |
|`set-env-var` |Sets, unsets, or blocks the value of a mock environment variable on a tag. |
|`set-rpm-macro` |Sets, unsets, or blocks the value of a mock RPM macro on a tag. |
|`swap—tag-inheritance` |Adjust the inheritance of a tag by replacing one entry for another. If both entries are already parents of a tag, then swap the priority of the two. |


## Information Commands

These commands are informational only, and do not require any special
permissions in koji.

| Command | Description |
|---------|-------------|
|`affected—targets` |Show targets which would be impacted by modifications to the given tag |
|`cginfo` |Show content generators and their permitted users |
|`check—hosts` |Show builder hosts which haven't been checking in lately |
|`check-repo` |Shows whether a tag's repo is up-to-date with its history |
|`client-config` |Show settings for client profiles |
|`filter-builds` |Filter a list of NVRs by various criteria |
|`filter-tags` |Filter a list of tags by various criteria |
|`latest-archives` |Show selected latest archives from a tag |
|`list-btypes` |Show build types |
|`list-build-archives` |Show selected archives attached to a build |
|`list-cgs` |Show content generators |
|`list-component-builds` |Show builds which were used to produce others |
|`list-env-vars` |Show all inherited mock environment variables for a tag |
|`list-rpm-macros` |Show all inherited mock RPM macros for a tag |
|`list-tag-extras` |Show all inherited extra fields for a tag |
|`open` |Opens a brower to the info page for koji data types |
|`perminfo` |Show information about a permission |
|`pull-container` |Pull an image from a container build |
|`repoquery` |Use DNF to query the contents of a tag's repo |
|`userinfo` |Show information about a user account |


## Install

The kojismokydingo package utilizes setuptools and can be built and
installed as a wheel.

Because of how koji loads client plugins, if you want the meta plugin
available by default system-wide, then the package needs to be
installed into the default site-packages for the python
installation.


### As an RPM via DNF

If using an RPM-based distribution, this is easily achieved using the
included spec to produce an RPM and install that.

```bash
make clean rpm
dnf install dist/noarch/python3-kojismokydingo-2.2.0-0.fc38.noarch.rpm
```


### As a System-wide Wheel via Pip

The pip3 tool can also achieve this by specifying the specific root or
prefix parameter

```bash
make clean build
pip3 install --prefix /usr -I dist/kojismokydingo-2.2.0-py3-none-any.whl
```

or you can install the most recent release straight from PyPI

```bash
pip3 install --prefix /usr -I kojismokydingo
```


### As a User-only Wheel via Pip

If you only want the plugin available for yourself, you can use the
`install` target of the Makefile to easily build the wheel, install it
using pip3, then symlink the meta plugin into your koji user plugins
directory.

```bash
make clean install
```

or you can install the most recent release straight from PyPI, and
then copy the meta plugin into place

```bash
pip3 install --user -I kojismokydingo
mkdir -p ~/.koji/plugins
cp $(python3 -c 'import koji_cli_plugins.kojismokydingometa as k ; print(k.__file__);' ~/.koji/plugins
```


## Contact

Author: Christopher O'Brien  <obriencj@gmail.com>

Original Git Repository: <https://github.com/obriencj/koji-smoky-dingo>

Documentation: <https://obriencj.github.io/koji-smoky-dingo>


## License

This library is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.

This library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this library; if not, see <http://www.gnu.org/licenses/>.
