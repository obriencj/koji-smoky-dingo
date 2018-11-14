# Overview of koji-smoky-dingo

This is a collection of simple client command-line plugins for [koji].

[koji]: https://pagure.io/koji


## Contents

The following commands are included


### Admin CLI Command: mass-tag

Quickly tag a large amount of builds, bypassing the creation of
individual tasks.

```bash
cat product-1.0-nvr-list.txt | koji mass-tag my-product-1.0-released --debug
```

This utility uses tagBuildBypass to tag the given builds without using
a full tagBuild task for each one. It will queue 100 builds at a time
up via multicalls as well. Prior to tagging, the command will verify
that a package listing exists for each given build name. If a matching
package entry isn't found, then one will be created, with ownership
belonging to the user that created the first build of that name in the
list of NVRs to be tagged.

Additional options allow sorting of the builds prior to being tagged,
and overriding an owner for any new package listings being created.


### Admin CLI Command: renum-tag (coming soon)

Adjust the priority values of a tag to maintain the same inheritance
order, but to create an even amount of space between each entry.


### Admin CLI Command: swap-inheritance (coming soon)

Adjust the inheritance of a tag by replacing one entry for another. If
both entries are already parents of a tag, then swap the priority of
the two.


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
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see
<http://www.gnu.org/licenses/>.
