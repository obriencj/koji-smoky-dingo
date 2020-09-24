koji list-cgs
=============

.. highlight:: none

::

 usage: koji list-cgs [-h] [--build NVR] [--json] [--quiet]

 List Content Generators

 optional arguments:
   -h, --help   show this help message and exit
   --build NVR  List the Content Generators used to produce a given build
   --json       Output as JSON
   --quiet, -q  Output just the CG names


List all available Content Generators in the koji instance, or for a
given build.


References
----------

* :py:obj:`kojismokydingo.cli.builds.ListCGs`
* :py:func:`kojismokydingo.cli.builds.cli_list_cgs`
