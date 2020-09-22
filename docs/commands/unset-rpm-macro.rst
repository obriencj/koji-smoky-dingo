koji unset-rpm-macro
====================

.. highlight:: none

::

 usage: koji unset-rpm-macro [-h] [--target] TAGNAME macro

 Unset an RPM Macro on a tag

 positional arguments:
   TAGNAME     Name of tag
   macro       Name of the macro

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


Removes an RPM macro definition from a tag.

Note that the definition must have been set directly on the given tag,
and not inherited from a parent tag. There is currently no way to
block or undefine an inherited RPM macro definition -- the closest is
setting it to ``%nil`` which may have undesireable side-effects as
well.

This command requires either the ``admin`` or ``tag`` permission,
as it modifies tag configuration data.

See also :ref:`koji list-rpm-macros`, :ref:`koji set-rpm-macro`


References
----------

* :py:obj:`kojismokydingo.cli.tags.UnsetRPMMacro`
* :py:func:`kojismokydingo.cli.tags.cli_unset_rpm_macro`
