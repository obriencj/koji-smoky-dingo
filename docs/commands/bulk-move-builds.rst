koji bulk-move-builds
=====================

.. highlight:: none

::

 usage: koji bulk-move-builds [-h] [-f NVR_FILE] [--create] [--strict]
                              [--owner OWNER] [--no-inherit] [--force]
                              [--notify] [-v] [--nvr-sort | --id-sort]
                              SRCTAG DESTTAG [NVR [NVR ...]]

 Move a large number of builds between tags

 positional arguments:
   SRCTAG                Tag to unassociate from builds
   DESTTAG               Tag to associate with builds
   NVR                   Build NVRs to move

 optional arguments:
   -h, --help            show this help message and exit
   -f NVR_FILE, --file NVR_FILE
                         Read list of builds from file, one NVR per line.
                         Specify - to read from stdin.
   --create              Create the tag if it doesn't exist already
   --strict              Stop processing at the first failure
   --owner OWNER         Force missing package listings to be created with the
                         specified owner
   --no-inherit          Do not use parent tags to determine existing package
                         listing.
   --force               Force tagging operations. Requires admin permission
   --notify              Send tagging notifications. This can be expensive for
                         koji hub, avoid unless absolutely necessary.
   -v, --verbose         Print tagging status

 Tagging order of builds:
   --nvr-sort            pre-sort build list by NVR, so highest NVR is tagged
                         last
   --id-sort             pre-sort build list by build ID, so most recently
                         completed build is tagged last


This command is used to facilitate the moving of larger amounts of
builds between tags, without the overhead of creating a task for each
NVR.

This will also intelligently add package listings to the destination
tag in the event that a build's package isn't listed already. The
owner for such a package listing can be specified via the ``--owner``
option. If left unspecified, the owner for the first build of that
package is used.

By default, this command will not trigger tagNotification tasks (which
cause an email to be sent to the package listing owner and the build
owner to let them know their build has been tagged). Sending such
notifications can easily bog down a koji hub, so this setting should
be left off unless it is absolutely necessary that such notifications
be triggered.

The set of NVRs to tag can be fed to this command in multiple
ways. They can be specified as arguments, or they can be specified
using the ``--file`` option to reference either a file containing a
list of NVRs (one per line) or ``-`` to indicate stdin. If NVRs are
specified on the command line and also via ``--file`` then the two
lists will be concatenated in that order.

If no NVRs are given as arguments, and the ``--file`` option isn't
specified, and stdin is detected to not be a TTY, then the list of
NVRs will be read from stdin.

By default the builds will be tagged in the order they are
specified. If there is not already some meaningful ordering to the
builds, it may be best to sort them by either NVR or ID, to ensure
"higher" builds will be considered latest according to normal koji tag
rules.


References
----------

* :py:obj:`kojismokydingo.cli.builds.BulkMoveBuilds`
* :py:func:`kojismokydingo.cli.builds.cli_bulk_move_builds`
* :py:func:`kojismokydingo.builds.bulk_move_builds`
* :py:func:`kojismokydingo.builds.iter_bulk_move_builds`
* :py:func:`kojismokydingo.builds.bulk_move_nvrs`
