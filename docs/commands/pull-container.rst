koji pull-container
===================

.. highlight:: none

::

 usage: koji pull-container [-h] [--latest-build TAG]
                            [--command COMMAND | --print]
                            BUILD [ARGS ...]

 Pull a container build's image

 positional arguments:
   BUILD                 Container build to pull
   ARGS                  all additional arguments after will be passed to the
                         configured container manager command. Specify -- to
                         prevent from being treated as a koji option.

 options:
   -h, --help            show this help message and exit
   --latest-build TAG    BUILD is a package name, use the matching latest build
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

The ``--latest-build=TAG`` option changes the behavior slightly.
Rather than specifying a build by its NVR, the build argument is now a
package name. The command then tries to find the latest build of the
matching package name in the given tag, and then pulls that
instead. It is similar to invoking with the build argument set to the
result of `koji latest-build TAG BUILD`


References
----------

* :py:obj:`kojismokydingo.cli.builds.PullContainer`
* :py:func:`kojismokydingo.cli.builds.cli_pull_container`
* `OSBS - Building Container Images - Get Build <https://osbs.readthedocs.io/en/latest/users.html#get-build>`_
* `Atomic Reactor - Koji Integration - Type-specific Metadata <https://github.com/containerbuildsystem/atomic-reactor/blob/master/docs/koji.md#type-specific-metadata>`_
