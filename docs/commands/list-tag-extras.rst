koji list-tag-extras
====================

.. highlight:: none

::

 usage: koji list-tag-extras [-h] [--target] [--blocked] [--quiet | --json]
                             TAGNAME

 Show extra settings for a tag

 positional arguments:
   TAGNAME      Name of tag

 optional arguments:
   -h, --help   show this help message and exit
   --target     Specify by target rather than a tag
   --blocked    Show blocked extras
   --quiet, -q  Omit headings
   --json       Output as JSON


Provides a list of tag extra settings, displaying the name and value
and the tag which provided the setting.


References
----------

* :py:obj:`kojismokydingo.cli.tags.ListTagExtras`
* :py:func:`kojismokydingo.cli.tags.cli_list_tag_extras`
