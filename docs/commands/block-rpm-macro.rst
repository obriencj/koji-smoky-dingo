koji block-rpm-macro
====================

.. highlight:: none

::

 usage: koji block-rpm-macro [-h] [--target] TAGNAME macro

 Block an RPM Macro from a tag

 positional arguments:
   TAGNAME     Name of tag
   macro       Name of the macro to block

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


This command is a convenience equivalent to ``koji set-rpm-macro --block``

See also :ref:`koji list-rpm-macros`, :ref:`koji set-rpm-macro`, :ref:`koji remove-rpm-macro`


References
----------

* :py:obj:`kojismokydingo.cli.tags.BlockRPMMacro`
* :py:func:`kojismokydingo.cli.tags.cli_set_rpm_macro`
