koji list-build-archives
========================

.. highlight:: none

::

 usage: koji list-build-archives [-h] [--show-deleted] [--json] [--urls]
                                 [--type TYPE | --rpm | --maven | --image | --win]
                                 [--archive-type EXT] [--arch ARCHES]
                                 [--key KEY] [--unsigned]
                                 NVR [NVR ...]

 List archives from a build

 positional arguments:
   NVR                 The NVR containing the archives

 optional arguments:
   -h, --help          show this help message and exit
   --show-deleted, -d  Show archives for a deleted build. Default, deleted
                       builds show an empty archive list
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


Print paths for archives and RPMs attached to a build.

Allows optional filtering based on the build type, archive type,
architecture, and available signatures.

The paths are based on the koji client configuration for the profile
in use, and so will start with the ``topdir`` value. If ``--urls`` is
specified, then the ``topurl`` value is used instead.


References
----------

* :py:obj:`kojismokydingo.cli.archives.ListBuildArchives`
* :py:func:`kojismokydingo.cli.archives.cli_list_build_archives`
