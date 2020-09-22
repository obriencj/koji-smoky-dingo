koji filter-builds
==================


.. highlight:: none

::

 usage: koji filter-builds [-h] [-f NVR_FILE] [--strict] [--tag TAG]
                           [--inherit] [--latest] [--nvr-sort | --id-sort]
                           [--lookaside LOOKASIDE]
                           [--shallow-lookaside SHALLOW_LOOKASIDE]
                           [--limit LIMIT] [--shallow-limit SHALLOW_LIMIT]
                           [--type BTYPES] [-c CG_NAME]
                           [--imports | --no-imports]
                           [nvr [nvr ...]]

 Filter a list of NVRs by various criteria

 positional arguments:
   nvr

 optional arguments:
   -h, --help            show this help message and exit
   -f NVR_FILE, --file NVR_FILE
                         Read list of builds from file, one NVR per line.
                         Specify - to read from stdin.
   --strict              Error if any of the NVRs do not resolve into a real
                         build. Otherwise, bad NVRs are ignored.

 Working from tagged builds:
   --tag TAG             Filter using the builds in this tag
   --inherit             Follow inheritance
   --latest              Limit to latest builds

 Sorting of output builds:
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


Given a list of NVRs, output only those which match a set of filtering
parameters.

The NVR list can also come from the contents of a tag.


References
----------

* :py:obj:`kojismokydingo.builds.BuildFilter`
* :py:obj:`kojismokydingo.cli.builds.FilterBuilds`
* :py:func:`kojismokydingo.cli.builds.cli_filter_builds`
