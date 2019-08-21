# Overview of koji-smoky-dingo

This is a collection of simple client command-line plugins for [koji].

[koji]: https://pagure.io/koji

The name "smoky-dingo" was provided by [coolname] and has no particular relevance.

[coolname]: https://pypi.org/project/coolname/


## Meta Plugin

This project is broken into two parts. The first part is a relatively
tiny CLI plugin for koji which acts as an adapter to load commands
registered via python's entry points. The second and larger part is a
collection of commands that are be loaded by that meta plugin.

The meta plugin can be used to load commands other than those provided
by koji-smoky-dingo. Simply register your commands with the
`"koji_smoky_dingo"` entry point key and install your package. See
[setup.py] for direct examples.

[setup.py]: https://github.com/obriencj/koji-smoky-dingo/blob/master/setup.py


## Admin Commands

These commands require the admin permission.

| Command | Description |
|---------|-------------|
|`bulk—tag-builds` |Quickly tag a large amount of builds, bypassing the creation of individual tasks. |


## Tag Commands

These commands modify tag features, requiring either the tag
permission (koji >= [1.18]) or the admin permission.

| Command | Description |
|---------|-------------|
|`renum—tag-inheritance` |Adjust the priority values of a tag to maintain the same inheritance order, but to create an even amount of space between each entry. |
|`swap—tag-inheritance` |Adjust the inheritance of a tag by replacing one entry for another. If both entries are already parents of a tag, then swap the priority of the two. |


## Informational Commands

These commands are informational only, and do not require any special
permissions in koji.

| Command | Description |
|---------|-------------|
|`affected—targets` |Show targets which would be impacted by modifications to the given tag |
|`check—hosts` |Show builder hosts which haven't been checking in lately |
|`list—imported` |Show builds which were imported into koji |
|`perminfo` |Show information about a permission |
|`userinfo` |Show information about a user account |


## Install

### Meta Plugin

Because of how koji loads client plugins, the meta plugin needs to be
installed with either the `--old-and-unmanageable` flag or with
`--root=/` specified.

```bash
sudo python setup-meta.py clean build install --root=/
```

With koji >= [1.18], the meta plugin can also be installed into
`~/.koji_cli_plugins`

[1.18]: https://docs.pagure.org/koji/release_notes_1.18/

```bash
mkdir -p ~/.koji/plugins
cp koji_cli_plugins/kojismokydingometa.py ~/.koji/plugins
```

### Package kojismokydingo

However the rest of koji-smoky-dingo can be installed normally, either
as a system-level or user-level package

```bash
# system install
sudo python setup.py install

# user only
python setup.py install --user
```


## Contact

Author: Christopher O'Brien  <obriencj@gmail.com>

Original Git Repository: <https://github.com/obriencj/koji-smoky-dingo>


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
