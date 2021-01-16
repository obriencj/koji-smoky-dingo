Overview
========

Koji Smoky Dingo is a collection of client command-line plugins for the
`Koji <https://pagure.io/koji>`__ build system, and a set of utility
modules for writing your own commands or scripts.

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
(koji >=
`1.18 <https://docs.pagure.org/koji/release_notes/release_notes_1.18/>`__)
or the admin permission.

+----------------------------+-----------------------------------------+
| Command                    | Description                             |
+============================+=========================================+
| ``block-env-var``          | Blocks a mock environment variable from |
|                            | a tag.                                  |
+----------------------------+-----------------------------------------+
| ``block-rpm-macro``        | Blocks a mock RPM macro from a tag.     |
+----------------------------+-----------------------------------------+
| ``bulk—tag-builds``        | Quickly tag a large amount of builds,   |
|                            | bypassing the creation of individual    |
|                            | tasks.                                  |
+----------------------------+-----------------------------------------+
| ``remove-env-var``         | Removes a mock environment variable     |
|                            | from a tag.                             |
+----------------------------+-----------------------------------------+
| ``remove-rpm-macro``       | Removes a mock RPM macro from a tag.    |
+----------------------------+-----------------------------------------+
| ``renum—tag-inheritance``  | Adjust the priority values of a tag to  |
|                            | maintain the same inheritance order,    |
|                            | but to create an even amount of space   |
|                            | between each entry.                     |
+----------------------------+-----------------------------------------+
| ``set-env-var``            | Sets, unsets, or blocks the value of a  |
|                            | mock environment variable on a tag.     |
+----------------------------+-----------------------------------------+
| ``set-rpm-macro``          | Sets, unsets, or blocks the value of a  |
|                            | mock RPM macro on a tag.                |
+----------------------------+-----------------------------------------+
| ``swap—tag-inheritance``   | Adjust the inheritance of a tag by      |
|                            | replacing one entry for another. If     |
|                            | both entries are already parents of a   |
|                            | tag, then swap the priority of the two. |
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
| ``cginfo``                 | Show content generators and their       |
|                            | permitted users                         |
+----------------------------+-----------------------------------------+
| ``check—hosts``            | Show builder hosts which haven’t been   |
|                            | checking in lately                      |
+----------------------------+-----------------------------------------+
| ``client-config``          | Show settings for client profiles       |
+----------------------------+-----------------------------------------+
| ``filter-builds``          | Filter a list of NVRs by various        |
|                            | criteria                                |
+----------------------------+-----------------------------------------+
| ``filter-tags``            | Filter a list of tags by various        |
|                            | criteria                                |
+----------------------------+-----------------------------------------+
| ``latest-archives``        | Show selected latest archives from a    |
|                            | tag                                     |
+----------------------------+-----------------------------------------+
| ``list-btypes``            | Show build types                        |
+----------------------------+-----------------------------------------+
| ``list-build-archives``    | Show selected archives attached to a    |
|                            | build                                   |
+----------------------------+-----------------------------------------+
| ``list-cgs``               | Show content generators                 |
+----------------------------+-----------------------------------------+
| ``list-component-builds``  | Show builds which were used to produce  |
|                            | others                                  |
+----------------------------+-----------------------------------------+
| ``list-env-vars``          | Show all inherited mock environment     |
|                            | variables for a tag                     |
+----------------------------+-----------------------------------------+
| ``list-rpm-macros``        | Show all inherited mock RPM macros for  |
|                            | a tag                                   |
+----------------------------+-----------------------------------------+
| ``list-tag-extras``        | Show all inherited extra fields for a   |
|                            | tag                                     |
+----------------------------+-----------------------------------------+
| ``open``                   | Opens a brower to the info page for     |
|                            | koji data types                         |
+----------------------------+-----------------------------------------+
| ``perminfo``               | Show information about a permission     |
+----------------------------+-----------------------------------------+
| ``userinfo``               | Show information about a user account   |
+----------------------------+-----------------------------------------+

Install
-------

The kojismokydingo package utilizes setuptools and can be built and
installed as an egg or wheel.

Because of how koji loads client plugins, if you want the meta plugin
available by default system-wide, then the package needs to be installed
into the default site-packages for the python installation.

Using RPM
~~~~~~~~~

If using an RPM-based distribution, this is easily achieved using the
included spec to produce an RPM and install that.

.. code:: bash

   make clean rpm
   dnf install dist/noarch/python3-kojismokydingo-0.9.7-0.fc32.noarch.rpm

System-wide Using Python
~~~~~~~~~~~~~~~~~~~~~~~~

Using traditional setuptools or pip installation methods can also
achieve this by specifying the specific root or prefix parameter

.. code:: bash

   # Python 2.6 global install
   sudo python setup.py clean build install --root=/

   # Python 2.7 global install
   python3 setup.py bdist_wheel
   pip3 install --prefix /usr -I dist/kojismokydingo-0.9.7-py2-none-any.whl

   # Python 3 global install
   python3 setup.py bdist_wheel
   pip3 install --prefix /usr -I dist/kojismokydingo-0.9.7-py3-none-any.whl

User-only Using Python
~~~~~~~~~~~~~~~~~~~~~~

However, if you only want the plugin available for yourself, you can
install it anywhere and tell koji to look in that particular
``site-package/koji_cli_plugins`` instance

.. code:: bash

   # Python 3 user install
   python3 setup.py bdist_wheel
   pip3 install --user -I dist/kojismokydingo-0.9.7-py3-none-any.whl

And the following setting in ~/.koji/config assuming Python version 3.7
– read the output of the install command above to verify your install
path. Note that the section title needs to match your koji profile, and
that you need to configure this setting for each profile you’ll want to
use the meta plugin with.

::

   [koji]
   plugin_paths = ~/.local/lib/python3.7/site-packages/koji_cli_plugins/

With koji >=
`1.18 <https://docs.pagure.org/koji/release_notes/release_notes_1.18/>`__,
the meta plugin can also be symlinked into ``~/.koji/plugins``

.. code:: bash

   mkdir -p ~/.koji/plugins
   ln -s ~/.local/lib/python3.7/site-packages/koji_cli_plugins/kojismokydingometa.py ~/.koji/plugins

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
