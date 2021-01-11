koji filter-builds
==================


.. highlight:: none

::

 usage: koji filter-builds [-h] [-f NVR_FILE] [--strict] [--tag TAG]
                           [--inherit] [--latest] [--nvr-sort | --id-sort]
                           [--lookaside LOOKASIDE]
                           [--shallow-lookaside SHALLOW_LOOKASIDE]
                           [--limit LIMIT] [--shallow-limit SHALLOW_LIMIT]
                           [--type BUILD_TYPE] [--rpm] [--maven] [--image]
                           [--win] [-c CG_NAME] [--imports | --no-imports]
                           [--completed | --deleted] [--param KEY=VALUE]
                           [--env-params] [--output FLAG:FILENAME]
                           [--no-entry-points]
                           [--filter FILTER | --filter-file FILTER_FILE]
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
   --no-entry-points, -n
                         Disable loading of additional sieves from entry_points
   --filter FILTER       Use the given sifty filter predicates
   --filter-file FILTER_FILE
                         Load sifty filter predictes from file


Given a list of NVRs, output only those which match a set of filtering
parameters.

The set of NVRs to filter can be fed to this command in multiple
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


Filtering Builds with Sifty Dingo
---------------------------------

This command supports filtering using the :ref:`Sifty Dingo Filtering
Language`. Sieve predicates can be specified inline using the
``--filter`` option or loaded from a file using the ``--filter-file``
option.

It's important to note that sifty dingo filtering only happens after
any conventional filtering has been applied, and thus only those
builds which have passed the conventional filters will be fed into the
sifter.


References
----------

* :py:obj:`kojismokydingo.cli.builds.FilterBuilds`
* :py:func:`kojismokydingo.cli.builds.cli_filter_builds`
* :py:obj:`kojismokydingo.builds.BuildFilter`
* :py:obj:`kojismokydingo.sift.builds`
