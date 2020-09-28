koji set-env-var
================

.. highlight:: none

::

 usage: koji set-env-var [-h] [--remove] [--block] [--target]
                         TAGNAME var [value]

 Set a mock environment variable on a tag

 positional arguments:
   TAGNAME     Name of tag
   var         Name of the environment variable
   value       Value of the environment var. Default: ''

 optional arguments:
   -h, --help  show this help message and exit
   --remove    Remove the environment var from the tag
   --block     Block the environment var from the tag
   --target    Specify by target rather than a tag


This command is a user-friendly alternative to using the ``koji
edit-tag`` to define extra settings prefixed with ``rpm.mock.`` Use of
this command requires either the ``admin`` or ``tag`` permission, as
it is mutating tag configuration data.

These settings are inheritable, so care must be taken not to
unintentionally pollute child build tags with settings they should not
have. When in doubt, use :ref:`koji affected-targets` to see what
build configurations may be impacted by any macro definitions.

When removing a defined environment variable, it must have been
defined directly on the given tag (ie. not inherited from a parent
tag).

The command :ref:`koji remove-env-var` is equivalent to ``koji
set-env-var --remove``

Blocking an environment variable prevents it from being defined
directly in the mock configuration. This is very different from
defining it as an empty string, as this allows system-level
definitions to be used instead. However, the ability to block tag
extra settings (including these environment variables) requires Koji
version 1.23 or later on the hub.

The command :ref:`koji block-env-var` is equivalent to ``koji
set-env-var --block``

See also :ref:`koji list-env-vars`


Examples
--------

.. highlight:: bash

::

 # The following are equivalent for setting a value for the CFLAGS
 # environment variable

 koji set-env-var my-tag-1.0-build CFLAGS=-Wno-shadow

 koji set-env-var my-tag-1.0-build CFLAGS '\-Wno-shadow'

 koji edit-tag my-tag-1.0-build --extra rpm.mock.CFLAGS=-Wno-shadow


 # The following are equivalent for removing the above defined CFLAGS
 # environment variable

 koji remove-env-var my-tag-1.0-build CFLAGS

 koji set-env-var my-tag-1.0-build CFLAGS --remove

 koji edit-tag my-tag-1.0-build --remove-extra rpm.mock.CFLAGS


 # The following are equivalent for blocking an inherited CFLAGS
 # environment variable without giving it some alternative value. This
 # feature requires koji 1.23 or greater.

 koji block-env-var my-tag-1.0-build CFLAGS

 koji set-env-var my-tag-1.0-build CFLAGS --block

 koji edit-tag my-tag-1.0-build --block-extra rpm.mock.CFLAGS


References
----------

* :py:obj:`kojismokydingo.cli.tags.SetEnvVar`
* :py:func:`kojismokydingo.cli.tags.cli_set_env_var`
