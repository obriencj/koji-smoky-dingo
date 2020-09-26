koji set-rpm-macro
==================

.. highlight:: none

::

 usage: koji set-rpm-macro [-h] [--target] TAGNAME macro [value]

 Set an RPM Macro on a tag

 positional arguments:
   TAGNAME     Name of tag
   macro       Name of the macro
   value       Value of the macro. Default: %nil

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


Defines an RPM macro on a tag.

This command is a user-friendly alternative to using `koji edit-tag` as defined in `Setting RPM Macros for Builds - Setting rpm.macro values <https://docs.pagure.org/koji/setting_rpm_macros/#setting-rpm-macro-values>`_

The underlying tag extra setting will be constructed with the prefix
``rpm.macro.`` and the macro name (minus any leading ``%``)

Empty RPM macro values are not permitted. The closest is ``%nil``
which is the default if no value is specified.

Note that RPM macros definitioned in this manner will take precedence
over any other definitions that may be provided by installed packages
in the buildroot.

These settings are inheritable, and there is currently no way to block
the inheritance of such a setting, so care must be taken not to
unintentionally pollute child build tags with settings they should not
have. When in doubt, use :ref:`koji affected-targets` to see what
build configurations may be impacted by any macro definitions.

This command requires either the ``admin`` or ``tag`` permission,
as it modifies tag configuration data.

See also :ref:`koji list-rpm-macros`, :ref:`koji unset-rpm-macro`


References
----------

* :py:obj:`kojismokydingo.cli.tags.SetRPMMacro`
* :py:func:`kojismokydingo.cli.tags.cli_set_rpm_macro`
