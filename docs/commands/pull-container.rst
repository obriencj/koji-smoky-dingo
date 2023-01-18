koji pull-container
===================

.. highlight:: none

::

 usage: koji pull-container [-h] [--latest-tagged TAG]
                            [--command COMMAND | --print]
                            build [args ...]

 Pull a container build's image

 positional arguments:
   build                 Container build to pull
   args                  all additional arguments after will be passed to the
                         configured container manager command. Specify -- to
                         prevent from being treated as a koji option.

 options:
   -h, --help            show this help message and exit
   --latest-tagged TAG   BUILD is a package name, use the matching latest build
                         in the given TAG
   --command COMMAND, -c COMMAND
                         Command to exec with the discovered pull spec
   --print, -p           Print pull spec to stdout rather than executing a
                         command


Used with builds produced by the OSBS content-generator. Identifies a
pullspec URI from the build extra metadata and invokes a configured
pull command (default ``podman pull {pullspec}``) to fetch a local
copy of the image.

Setting the pull command to ``-`` or using the ``--print`` option will
cause the pullspec to be printed to stdout.


References
----------

* :py:obj:`kojismokydingo.cli.build.PullContainer`
* :py:func:`kojismokydingo.cli.build.cli_pull_container`
* `OSBS - Building Container Images - Get Build<https://osbs.readthedocs.io/en/latest/users.html#get-build>`_
* `Atomic Reactor - Koji Integration - Type-specific Metadata <https://github.com/containerbuildsystem/atomic-reactor/blob/master/docs/koji.md#type-specific-metadata>`_
