koji remove-rpm-macro
=====================

.. highlight:: none

::

 usage: koji remove-rpm-macro [-h] [--target] TAGNAME macro

 Remove an RPM Macro from a tag

 positional arguments:
   TAGNAME     Name of tag
   macro       Name of the macro to remove

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


This command is a convenience equivalent to ``koji set-rpm-macro --remove``

See also :ref:`koji list-rpm-macros`, :ref:`koji set-rpm-macro`, :ref:`koji block-rpm-macro`


References
----------

* :py:obj:`kojismokydingo.cli.tags.RemoveRPMMacro`
* :py:func:`kojismokydingo.cli.tags.cli_set_rpm_macro`
