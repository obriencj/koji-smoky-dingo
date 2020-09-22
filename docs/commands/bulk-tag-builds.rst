koji bulk-tag-builds
====================

.. highlight:: none

::

 usage: koji bulk-tag-builds [-h] [-v] [--owner OWNER] [--no-inherit]
                             [-f NVR_FILE] [--strict] [--force] [--notify]
                             [--nvr-sort | --id-sort]
                             TAGNAME

 Quickly tag a large number of builds

 positional arguments:
   TAGNAME               Tag to associate builds with

 optional arguments:
   -h, --help            show this help message and exit
   -v, --verbose         Print debugging information
   --owner OWNER         Force missing package listings to be created with the
                         specified owner
   --no-inherit          Do not use parent tags to determine existing package
                         listing.
   -f NVR_FILE, --file NVR_FILE
                         Read list of builds from file, one NVR per line. Omit
                         for default behavior: read build NVRs from stdin
   --strict              Stop processing at the first failure
   --force               Force tagging.
   --notify              Send tagging notifications.

 Tagging order of builds:
   --nvr-sort            pre-sort build list by NVR, so highest NVR is tagged
                         last
   --id-sort             pre-sort build list by build ID, so most recently
                         completed build is tagged last

References
----------

* :py:obj:`kojismokydingo.cli.builds.BulkTagBuilds`
* :py:func:`kojismokydingo.cli.builds.cli_bulk_tag_builds`
