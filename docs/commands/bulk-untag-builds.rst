koji bulk-untag-builds
======================

.. highlight:: none

::

 usage: koji bulk-untag-builds [-h] [-f NVR_FILE] [--strict] [--force]
                               [--notify] [-v]
                               TAGNAME [NVR [NVR ...]]

 Untag a large number of builds

 positional arguments:
   TAGNAME               Tag to unassociate from builds
   NVR                   Build NVRs to untag

 optional arguments:
   -h, --help            show this help message and exit
   -f NVR_FILE, --file NVR_FILE
                         Read list of builds from file, one NVR per line.
                         Specify - to read from stdin.
   --strict              Stop processing at the first failure
   --force               Force untagging operations. Requires admin permission
   --notify              Send untagging notifications. This can be expensive for
                         koji hub, avoid unless absolutely necessary.
   -v, --verbose         Print untagging status


This command is used to facilitate the untagging of larger amounts of
builds, without the overhead of creating an untagBuild task for each
NVR.

By default, this command will not trigger untagNotification tasks
(which cause an email to be sent to the package listing owner and the
build owner to let them know their build has been tagged). Sending
such notifications can easily bog down a koji hub, so this setting
should be left off unless it is absolutely necessary that such
notifications be triggered.

The set of NVRs to untag can be fed to this command in multiple
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

* :py:obj:`kojismokydingo.cli.builds.BulkUntagBuilds`
* :py:func:`kojismokydingo.cli.builds.cli_bulk_untag_builds`
* :py:func:`kojismokydingo.builds.bulk_untag_builds`
* :py:func:`kojismokydingo.builds.iter_bulk_untag_builds`
* :py:func:`kojismokydingo.builds.bulk_untag_nvrs`
