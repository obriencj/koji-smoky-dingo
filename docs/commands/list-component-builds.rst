koji list-component-builds
==========================

.. highlight:: none

::

 usage: koji list-component-builds [-h] [-f NVR_FILE] [--tag TAG] [--inherit]
                                   [--latest] [--nvr-sort | --id-sort]
                                   [--lookaside LOOKASIDE]
                                   [--shallow-lookaside SHALLOW_LOOKASIDE]
                                   [--limit LIMIT]
                                   [--shallow-limit SHALLOW_LIMIT]
                                   [--type BTYPES] [-c CG_NAME]
                                   [--imports | --no-imports]
                                   [--completed | --deleted]
                                   [NVR [NVR ...]]

 List a build's component dependencies

 positional arguments:
   NVR                   Build NVRs to list components of

 optional arguments:
   -h, --help            show this help message and exit
   -f NVR_FILE, --file NVR_FILE
                         Read list of builds from file, one NVR per line.
                         Specify - to read from stdin.

 Components of tagged builds:
   --tag TAG             Look for components of builds in this tag
   --inherit             Follow inheritance
   --latest              Limit to latest builds

 Sorting of builds:
   --nvr-sort            Sort output by NVR in ascending order
   --id-sort             Sort output by Build ID in ascending order

 Filtering by tag:
   --lookaside LOOKASIDE
                         Omit builds found in this tag or its parent tags
   --shallow-lookaside SHALLOW_LOOKASIDE
                         Omit builds found directly in this tag
   --limit LIMIT         Limit results to builds found in this tag or its
                         parent tags
   --shallow-limit SHALLOW_LIMIT
                         Limit results to builds found directly in this tag

 Filtering by type:
   --type BTYPES         Limit to builds of this BType
   -c CG_NAME, --content-generator CG_NAME
                         show content generator imports by build system name.
                         Default: display no CG builds. Specify 'any' to see CG
                         imports from any system. May be specified more than
                         once.
   --imports             Limit to imported builds
   --no-imports          Invert the imports checking

 Filtering by state:
   --completed           Limit to completed builds
   --deleted             Limit to deleted builds


This command identifies the builds used to produce another build.

The set of NVRs to tag can be fed to this command in multiple
ways. They can be specified as arguments, or they can be specified
using the ``--file`` option to reference either a file containing a
list of NVRs (one per line) or ``-`` to indicate stdin. If NVRs are
specified on the command line and also via ``--file`` then the two
lists will be concatenated in that order.

If no NVRs are given as arguments, and the ``--file`` option isn't
specified, and stdin is detected to not be a TTY, then the list of
NVRs will be read from stdin.


References
----------

* :py:obj:`kojismokydingo.cli.builds.ListComponents`
* :py:func:`kojismokydingo.cli.builds.cli_list_components`
