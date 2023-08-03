koji pull-container
===================

.. highlight:: none

::

 usage: koji pull-container [-h] [--latest-build KOJI_TAG]
                            [--command PULL_COMMAND | --print]
                            [--tag-command TAG_COMMAND | --no-tag]
                            BUILD

 Pull a container build's image

 positional arguments:
   BUILD                 Container build to pull

 options:
   -h, --help            show this help message and exit
   --latest-build KOJI_TAG
                         BUILD is a package name, use the matching latest build
                         in the given koji tag
   --command PULL_COMMAND
                         Command to exec with the discovered pull spec
   --print, -p           Print pull spec to stdout rather than executing a
                         command
   --tag-command TAG_COMMAND
                         Command to exec after pulling the image
   --no-tag, -n          Do not execute the tag command after pulling the image


Used with builds produced by the OSBS content-generator. Identifies a
pullspec URI from the build extra metadata and invokes a configured
pull command to fetch a local copy of the image. If that pull command
was successful, then the configured tag command is invoked to provide
a convenient local reference.

Setting the pull command to ``-`` or using the ``--print`` option will
cause the pullspec to be printed to stdout.

Setting the tag command to ``-`` or using the ``--no-tag`` or
``--print`` options will skip the local tagging step.

The ``--latest-build=TAG`` option changes the behavior slightly.
Rather than specifying a build by its NVR, the build argument is now
treated as a package name. The command then tries to find the latest
build of the matching package name in the given tag, and then pulls
that instead. It is similar to invoking with the build argument set to
the result of ``koji latest-build KOJI_TAG BUILD``

Introduced in version 2.0.0


Configuration
-------------

The default values for the pull and tag commands can also be set under
the ``[pull-container]`` plugin configuration using the settings
``pull_command`` and ``tag_command``

eg. in ``~/.config/ksd/common.conf``

::

   [pull-container]
   # these are also the default values if left unspecified
   pull_command = podman pull {pullspec}
   tag_command = podman image tag {pullspec} {profile}/{nvr}


The pull command only accepts the ``{pullspec}`` variable.

The tag command accepts the ``{pullspec}``, ``{profile}``, and
``{nvr}`` variables. The profile is the name of the current koji
profile that the command is invoked with. The nvr varialbe is the
discovered koji build's NVR.


References
----------

* :py:obj:`kojismokydingo.cli.builds.PullContainer`
* :py:func:`kojismokydingo.cli.builds.cli_pull_container`
* `OSBS - Building Container Images - Get Build <https://osbs.readthedocs.io/en/latest/users.html#get-build>`_
* `Atomic Reactor - Koji Integration - Type-specific Metadata <https://github.com/containerbuildsystem/atomic-reactor/blob/master/docs/koji.md#type-specific-metadata>`_
