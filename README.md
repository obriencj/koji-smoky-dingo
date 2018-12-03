# Overview of koji-smoky-dingo

This is a collection of simple client command-line plugins for [koji].

[koji]: https://pagure.io/koji

The name "smoky-dingo" was provided by [coolname] and has no particular relevance.

[coolname]: https://pypi.org/project/coolname/


## Admin Commands

The following client commands are included with koji-smoky-dingo and
require admin permissions to function.

| Command | Description |
|`koji mass-tag` |Quickly tag a large amount of builds, bypassing the creation of individual tasks. |
|`koji renum-tag` |Adjust the priority values of a tag to maintain the same inheritance order, but to create an even amount of space between each entry. |
|`koji swap-inheritance` |Adjust the inheritance of a tag by replacing one entry for another. If both entries are already parents of a tag, then swap the priority of the two. |


## Anon Commands

The following client commands are included with koji-smoky-dingo and
do not require any special permissions to function.853774

| Command | Description |
|`koji userinfo` |Show information and permissions for a koji user account |


## Install

Because of how koji loads client plugins, this package needs to be
installed with either the `--old-and-unmanageable` flag or with
`--root=/` specified.

```bash
sudo python setup.py clean build install --root=/
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
