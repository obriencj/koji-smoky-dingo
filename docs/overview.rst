Overview
========

Koji Smoky Dingo is a collection of client command-line plugins for
`koji <https://pagure.io/koji>`__, and a set of utility modules for
writing your own commands or scripts.

The phrase “smoky-dingo” was provided by
`coolname <https://pypi.org/project/coolname/>`__ and has no particular
relevance.

Meta Plugin
-----------

This project provides a relatively tiny CLI plugin for koji, named
kojismokydingometa. This plugin acts as an adapter between koji’s
existing CLI framework and Python’s entry_points. This adaptive behavior
is utilized by the rest of the project to add its own additional
commands to koji.

The meta plugin can be used to load commands other than those provided
as part of this project. Simply register your commands with the
``"koji_smoky_dingo"`` entry point key. See the example command’s
`setup.py <https://github.com/obriencj/koji-smoky-dingo/blob/master/examples/command/setup.py>`__
for a direct reference.

Tag Commands
------------

These commands modify tag features, requiring either the tag permission
(koji >= `1.18 <https://docs.pagure.org/koji/release_notes_1.18/>`__) or
the admin permission.

+----------------------------+-----------------------------------------+
| Command                    | Description                             |
+============================+=========================================+
| ``bulk—tag-builds``        | Quickly tag a large amount of builds,   |
|                            | bypassing the creation of individual    |
|                            | tasks.                                  |
+----------------------------+-----------------------------------------+
| ``renum—tag-inheritance``  | Adjust the priority values of a tag to  |
|                            | maintain the same inheritance order,    |
|                            | but to create an even amount of space   |
|                            | between each entry.                     |
+----------------------------+-----------------------------------------+
| ``set-env-var``            | Sets the value of a mock environment    |
|                            | variable on a tag.                      |
+----------------------------+-----------------------------------------+
| ``set-rpm-macro``          | Sets the value of a mock RPM macro on a |
|                            | tag.                                    |
+----------------------------+-----------------------------------------+
| ``swap—tag-inheritance``   | Adjust the inheritance of a tag by      |
|                            | replacing one entry for another. If     |
|                            | both entries are already parents of a   |
|                            | tag, then swap the priority of the two. |
+----------------------------+-----------------------------------------+
| ``unset-env-var``          | Removes a mock environment variable     |
|                            | from a tag.                             |
+----------------------------+-----------------------------------------+
| ``unset-rpm-macro``        | Removes a mock RPM macro from a tag.    |
+----------------------------+-----------------------------------------+

Information Commands
--------------------

These commands are informational only, and do not require any special
permissions in koji.

+----------------------------+-----------------------------------------+
| Command                    | Description                             |
+============================+=========================================+
| ``affected—targets``       | Show targets which would be impacted by |
|                            | modifications to the given tag          |
+----------------------------+-----------------------------------------+
| ``check—hosts``            | Show builder hosts which haven’t been   |
|                            | checking in lately                      |
+----------------------------+-----------------------------------------+
| ``client-config``          | Show settings for client profiles       |
+----------------------------+-----------------------------------------+
| ``latest-archives``        | Show selected latest archives from a    |
|                            | tag                                     |
+----------------------------+-----------------------------------------+
| ``list-build-archives``    | Show selected archives attached to a    |
|                            | build                                   |
+----------------------------+-----------------------------------------+
| ``list-cgs``               | Show content generators and their       |
|                            | permitted users                         |
+----------------------------+-----------------------------------------+
| ``list-env-vars``          | Shows all inherited mock environment    |
|                            | variables for a tag                     |
+----------------------------+-----------------------------------------+
| ``list—imported``          | Show builds which were imported into    |
|                            | koji                                    |
+----------------------------+-----------------------------------------+
| ``list-rpm-macros``        | Show all inherited mock RPM macros for  |
|                            | a tag                                   |
+----------------------------+-----------------------------------------+
| ``list-tag-extras``        | Show all inherited extra fields for a   |
|                            | tag                                     |
+----------------------------+-----------------------------------------+
| ``perminfo``               | Show information about a permission     |
+----------------------------+-----------------------------------------+
| ``userinfo``               | Show information about a user account   |
+----------------------------+-----------------------------------------+

Install
-------

The Meta Plugin
~~~~~~~~~~~~~~~

Because of how koji loads client plugins, the meta plugin needs to be
installed with either the ``--old-and-unmanageable`` flag or with
``--root=/`` specified.

.. code:: bash

   # system install
   sudo python setup-meta.py clean build install --root=/

With koji >=
`1.18 <https://docs.pagure.org/koji/release_notes_1.18/>`__, the meta
plugin can also be installed into ``~/.koji/plugins``

.. code:: bash

   # user only
   mkdir -p ~/.koji/plugins
   cp koji_cli_plugins/kojismokydingometa.py ~/.koji/plugins

The kojismokydingo Package
~~~~~~~~~~~~~~~~~~~~~~~~~~

However the rest of koji-smoky-dingo can be installed normally, either
as a system-level or user-level package.

.. code:: bash

   # system install
   sudo python setup.py install

   # user only
   python setup.py install --user

If deploying on a Python 3 environment, it’s best to install via pip

.. code:: bash

   # system insall
   python3 ./setup.py bdist_wheel
   pip3 install --I dist/*.whl

   # user only
   python3 ./setup.py bdist_wheel
   pip3 install --user --I dist/*.whl

Contact
-------

Author: Christopher O’Brien obriencj@gmail.com

Original Git Repository: https://github.com/obriencj/koji-smoky-dingo

Documentation: https://obriencj.github.io/koji-smoky-dingo

License
-------

This library is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

This library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this library; if not, see http://www.gnu.org/licenses/.
