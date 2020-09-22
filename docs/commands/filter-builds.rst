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
                           [--imports | --no-imports] [--completed | --deleted]
                           [NVR [NVR ...]]

 Filter a list of NVRs by various criteria

 positional arguments:
   NVR

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

 Filtering by state:
   --completed           Limit to completed builds
   --deleted             Limit to deleted builds


Given a list of NVRs, output only those which match a set of filtering
parameters.

The set of NVRs to tag can be fed to this command in multiple
ways. They can be specified as arguments, or they can be specified
using the ``--file`` option to reference either a file containing a
list of NVRs (one per line) or ``-`` to indicate stdin. The NVR list
can also come from the contents of a tag via the ``--tag`` option.

If NVRs are specified multiple ways, then they will be concatenated
into a single list. The order will be arguments, then ``--file``, and
then ``--tag``.

If no NVRs are given as arguments, and the ``--file`` option isn't
specified, and the ``--tag`` option isn't specified, and stdin is
detected to not be a TTY, then the list of NVRs will be read from
stdin.


References
----------

* :py:obj:`kojismokydingo.cli.builds.FilterBuilds`
* :py:func:`kojismokydingo.cli.builds.cli_filter_builds`
* :py:obj:`kojismokydingo.builds.BuildFilter`
