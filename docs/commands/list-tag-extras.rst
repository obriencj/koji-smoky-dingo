koji list-tag-extras
====================

.. highlight:: none

::

 usage: koji list-tag-extras [-h] [--target] [--quiet | --json] TAGNAME

 Show extra settings for a tag

 positional arguments:
   TAGNAME      Name of tag

 optional arguments:
   -h, --help   show this help message and exit
   --target     Specify by target rather than a tag
   --quiet, -q  Omit headings
   --json       Output as JSON


References
----------

* :py:obj:`kojismokydingo.cli.tags.ListTagExtras`
* :py:func:`kojismokydingo.cli.tags.cli_list_tag_extras`
