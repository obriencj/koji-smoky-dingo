koji list-component-builds
==========================

.. highlight:: none

::

 usage: koji list-component-builds [-h] [-f NVR_FILE] [--strict] [--tag TAG]
                                   [--inherit] [--latest]
                                   [--nvr-sort | --id-sort]
                                   [--lookaside LOOKASIDE]
                                   [--shallow-lookaside SHALLOW_LOOKASIDE]
                                   [--limit LIMIT]
                                   [--shallow-limit SHALLOW_LIMIT]
                                   [--type BUILD_TYPE] [--rpm] [--maven]
                                   [--image] [--win] [-c CG_NAME]
                                   [--imports | --no-imports]
                                   [--completed | --deleted]
                                   [--param KEY=VALUE] [--env-params]
                                   [--output FLAG:FILENAME]
                                   [--filter FILTER | --filter-file FILTER_FILE]
                                   [NVR [NVR ...]]

 List a build's component dependencies

 positional arguments:
   NVR                   Build NVRs to list components of

 optional arguments:
   -h, --help            show this help message and exit
   -f NVR_FILE, --file NVR_FILE
                         Read list of builds from file, one NVR per line.
                         Specify - to read from stdin.
   --strict              Error if any of the NVRs do not resolve into a real
                         build. Otherwise, bad NVRs are ignored.

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
   --type BUILD_TYPE     Limit to builds with this BType. May be specified
                         multiple times to allow for more than one type.
   --rpm                 Synonym for --type=rpm
   --maven               Synonym for --type=maven
   --image               Synonym for --type=image
   --win                 Synonym for --type=win

 Filtering by origin:
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

 Filtering with Sifty sieves:
   --param KEY=VALUE, -P KEY=VALUE
                         Provide compile-time values to the sifty filter
                         expressions
   --env-params          Use environment vars for params left unassigned
   --output FLAG:FILENAME, -o FLAG:FILENAME
                         Divert results marked with the given FLAG to FILENAME.
                         If FILENAME is '-', output to stdout. The 'default'
                         flag is output to stdout by default, and other flags
                         are discarded
   --filter FILTER       Use the given sifty filter predicates
   --filter-file FILTER_FILE
                         Load sifty filter predictes from file


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
