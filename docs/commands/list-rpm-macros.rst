koji list-rpm-macros
====================

.. highlight:: none

::

 usage: koji list-rpm-macros [-h] [--target]
                             [--quiet | --macro-definition | --json]
                             TAGNAME

 Show RPM Macros for a tag

 positional arguments:
   TAGNAME               Name of tag

 optional arguments:
   -h, --help            show this help message and exit
   --target              Specify by target rather than a tag
   --quiet, -q           Omit headings
   --macro-definition, -d
                         Output as RPM macro definitions
   --json                Output as JSON


Koji 1.18 and later support defining RPM macros via mock as part of a
tag's configuration metadata.

This command presents a filtered view of the tag's extras field,
limited to just those extra settings prefixed with ``rpm.macro.``

If the ``--macro-definition`` option is given, then the settings will be
displayed in the normal format of RPM macro definitions, eg.

::

 [nowhere]$ koji list-rpm-macros ruby-1.9.3-el6-build
 Macro  Value    Tag
 -----  -------  -----------------------
 dist   .el6     epel-6-build
 scl    ruby193  ruby-1.9.3-el6-build

 [nowhere]$ koji list-rpm-macros -d ruby-1.9.3-el6-build
 %dist .el6
 %scl ruby193


See also :ref:`koji set-rpm-macro`, :ref:`koji unset-rpm-macro`


References
----------

* :py:obj:`kojismokydingo.cli.tags.ListRPMMacros`
* :py:func:`kojismokydingo.cli.tags.cli_list_rpm_macros`
* :py:func:`kojismokydingo.tags.collect_tag_extras`
