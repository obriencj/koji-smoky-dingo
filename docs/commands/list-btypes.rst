koji list-btypes
================


.. highlight:: none

::

 usage: koji list-btypes [-h] [--build NVR] [--json] [--quiet]

 List BTypes

 optional arguments:
   -h, --help   show this help message and exit
   --build NVR  List the BTypes in a given build
   --json       Output as JSON
   --quiet, -q  Output just the BType names


List the available BTypes (build types) in the koji instance.

If the ``--build`` option is specified, then output only those types
present in the given build.


References
----------

* :py:obj:`kojismokydingo.cli.builds.ListBTypes`
* :py:func:`kojismokydingo.cli.builds.cli_list_btypes`
