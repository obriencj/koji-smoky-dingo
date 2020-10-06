koji latest-archives
====================

.. highlight:: none

::

 usage: koji latest-archives [-h] [--noinherit] [--json] [--urls]
                             [--type TYPE | --rpm | --maven | --image | --win]
                             [--archive-type EXT] [--arch ARCHES] [--key KEY]
                             [--unsigned]
                             TAGNAME

 List latest archives from a tag

 positional arguments:
   TAGNAME             The tag containing the archives

 optional arguments:
   -h, --help          show this help message and exit
   --noinherit         Do not follow inheritance
   --json              Output archive information as JSON
   --urls, -U          Present archives as URLs using the configured topurl.
                       Default: use the configured topdir

 Build Filtering Options:
   --type TYPE         Only show archives for the given build type. Example
                       types are rpm, maven, image, win. Default: show all
                       archives.
   --rpm               Synonym for --type=rpm
   --maven             Synonym for --type=maven
   --image             Synonym for --type=image
   --win               Synonym for --type=win

 Archive Filtering Options:
   --archive-type EXT  Only show archives with the given archive type. Can be
                       specified multiple times. Default: show all
   --arch ARCHES       Only show archives with the given arch. Can be specified
                       multiple times. Default: show all

 RPM Options:
   --key KEY, -k KEY   Only show RPMs signed with the given key. Can be
                       specified multiple times to indicate any of the keys is
                       valid. Preferrence is in order defined. Default: show
                       unsigned RPMs
   --unsigned          Allow unsigned copies if no signed copies are found when
                       --key=KEY is specified. Otherwise if keys are specified,
                       then only RPMs signed with one of those keys are shown.


This command retrieves a list of archives and RPMs from the latest
builds of a tag and displays their full paths.

The classification of what is "latest" varies slightly for builds with
the maven BType, as they are expected to include multiple versions of
the same group and artifact depending on the tag's settings.

The paths are based on the koji client configuration for the profile
in use, and so will start with the ``topdir`` value. If ``--urls`` is
specified, then the ``topurl`` value is used instead.


RPM Signatures
--------------

This command offers the ability to refer to the signed copy of any
RPMs discovered. By setting the ``--key`` option to a signature
fingerprint, then only RPMs which have been signed with that key will
be presented. A series of keys can be given by specifying the option
multiple times, which will be used as an order-of-preference list of
signatures. If falling back to an unsigned copy is desireable in
situations where none of the preferred signatures have been used, then
the ``--unsigned`` option can be specified.

Note that koji will report that RPMs have been signed, but may choose
to optimize volume storage by deleting the full signed copy of the
RPM. In this case, the path as reported may not actually exist. In
this event, it's possible to use the ``koji write-signed-rpm``
command to request that the signed copy is written out to disk again
based on the cached signature headers.


References
----------

* :py:obj:`kojismokydingo.cli.archives.LatestArchives`
* :py:func:`kojismokydingo.cli.archives.cli_latest_archives`
