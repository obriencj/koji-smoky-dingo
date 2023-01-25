koji check-repo
===============

.. highlight:: none

::

 usage: koji check-repo [-h] [--target] [--quiet | --verbose] [--utc]
                        [--events]
                        TAGNAME

 Check the freshness of a tag's repo

 positional arguments:
   TAGNAME        Name of tag

 optional arguments:
   -h, --help     show this help message and exit
   --target       Specify by target rather than a tag
   --quiet, -q    Suppress output
   --verbose, -v  Show history modifications since repo creation

 verbose output settings:
   --utc          Display timestamps in UTC rather than local time.
                  Requires koji >= 1.27
   --events, -e   Display event IDs


This command is used to identify whether a tag's repo is out-of-date
relative to the configuration or builds of the tag or its parents.

In addition to determining whether the repo is fresh or stale, the
``--verbose`` may be specified to output the combined history of all
tags in the inheritance past the point that the current repo was
created. This allows review of what changes may have happened between
then and now.
