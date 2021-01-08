koji filter-tags
================


.. highlight:: none

::

 usage: koji filter-tags [-h] [-f TAG_FILE] [--strict]
                         [--search GLOB | --regex REGEX]
                         [--nvr-sort | --id-sort] [--param KEY=VALUE]
                         [--env-params] [--output FLAG:FILENAME]
                         [--filter FILTER | --filter-file FILTER_FILE]
                         [TAGNNAME [TAGNNAME ...]]

 Filter a list of tags

 positional arguments:
   TAGNNAME              Tag names to filter through

 optional arguments:
   -h, --help            show this help message and exit
   -f TAG_FILE, --file TAG_FILE
                         Read list of tags from file, one name per line.
                         Specify - to read from stdin.
   --strict              Erorr if any of the tag names to not resolve into a
                         real tag. Otherwise, missing tags are ignored.

 Searching for tags:
   --search GLOB         Filter the results of a search for tags with the given
                         name pattern
   --regex REGEX         Filter the results of a search for tags with the given
                         regex name pattern

 Sorting of tags:
   --nvr-sort            Sort output by Name in ascending order
   --id-sort             Sort output by Tag ID in ascending order

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


Given a list of tag names, output only those which match a set of
filtering parameters.

The set of tags to filter can be fed to this command in multiple
ways. They can be specified as arguments, or they can be specified by
using the ``--file`` option to reference either a file containing a
list of tags (one per line) or ``-`` to indicate stdin. The tag list
can also be fed from a glob-style name search via the ``--search``
option, or a regex-style name search via the ``--regex`` option.

If no tags are given as arguments, and the ``--file`` option isn't
specified, and stdin is detected to not be a TTY, then the list of
tags will be read from stdin by default.


Filtering Tags with Sifty Dingo
-------------------------------

This command supports filtering using the :ref:`Sifty Dingo Filtering
Language`. Sieve predicates can be specified inline using the
``--filter`` option or loaded from a file using the ``--filter-file``
option.

It's important to note that sifty dingo filtering only happens after
the tags have been loaded from koji. The filters themselves are run
client-side.


References
----------

* :py:obj:`kojismokydingo.cli.tags.FilterTags`
* :py:func:`kojismokydingo.cli.tags.cli_filter_tags`
* :py:obj:`kojismokydingo.sift.tags`
