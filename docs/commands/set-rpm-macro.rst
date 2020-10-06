koji set-rpm-macro
==================

.. highlight:: none

::

 usage: koji set-rpm-macro [-h] [--remove] [--block] [--target]
                           TAGNAME macro [value]

 Set an RPM Macro on a tag

 positional arguments:
   TAGNAME     Name of tag
   macro       Name of the macro
   value       Value of the macro. Default: %nil

 optional arguments:
   -h, --help  show this help message and exit
   --remove    Remove the macro definition from the tag
   --block     Block the macro definition from the tag
   --target    Specify by target rather than a tag


Configures RPM macro settings on a tag.

Koji 1.18 and later support defining RPM macros via mock as part of a
tag's configuration metadata.

Koji 1.23 and later also support blocking such settings from being
inherited.

This command is a user-friendly alternative to using the ``koji
edit-tag`` command as defined in `Setting RPM Macros for Builds -
Setting rpm.macro values
<https://docs.pagure.org/koji/setting_rpm_macros/#setting-rpm-macro-values>`_.
Use of this command requires either the ``admin`` or ``tag``
permission, as it is mutating tag configuration data.

The underlying tag extra setting will be constructed with the prefix
``rpm.macro.`` and the macro name (minus any leading ``%``)

Empty RPM macro values are not permitted. The closest no an empty
value is ``%nil`` which is used as the default value if not otherwise
specified.

Note that RPM macros definined in this manner will take precedence
over any other definitions that may be provided by installed packages
in the buildroot.

These settings are inheritable, so care must be taken not to
unintentionally pollute child build tags with settings they should not
have. When in doubt, use :ref:`koji affected-targets` to see what
build configurations may be impacted by any macro definitions.

See also :ref:`koji list-rpm-macros`


Examples
--------

.. highlight:: bash

::

 # The following are equivalent for setting a value for the %dist
 # rpm macro

 koji set-env-var my-tag-1.0-build dist .el8

 koji set-env-var my-tag-1.0-build %dist .el8

 koji edit-tag my-tag-1.0-build --extra rpm.macro.dist=.el8


 # The following are equivalent for removing the above defined %dist
 # rpm macro

 koji remove-env-var my-tag-1.0-build dist

 koji set-env-var my-tag-1.0-build dist --remove

 koji edit-tag my-tag-1.0-build --remove-extra rpm.macro.dist


 # The following are equivalent for blocking an inherited %dist
 # macro without giving it some alternative value. This feature
 # requires koji 1.23 or greater.

 koji block-env-var my-tag-1.0-build dist

 koji set-env-var my-tag-1.0-build dist --block

 koji edit-tag my-tag-1.0-build --block-extra rpm.macro.dist


References
----------

* :py:obj:`kojismokydingo.cli.tags.SetRPMMacro`
* :py:func:`kojismokydingo.cli.tags.cli_set_rpm_macro`
