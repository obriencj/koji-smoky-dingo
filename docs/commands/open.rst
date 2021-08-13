koji open
=========

.. highlight:: none

::

 usage: koji open [-h] [--command COMMAND | --print] TYPE KEY

 Launch web UI for koji data elements

 positional arguments:
   TYPE                  The koji data element type. Supported types: archive,
                         build, build-dir, channel, host, package, repo, rpm,
                         tag, tag-latest-dir, tag-repo-dir, target, task, user
   KEY                   The key for the given element type.

 optional arguments:
   -h, --help            show this help message and exit
   --command COMMAND, -c COMMAND
                         Command to exec with the discovered koji web URL
   --print, -p           Print URL to stdout rather than executing a command


Launch local web browser to the informational page for a given koji data
element.

The types ``archive``, ``build``, ``channel``, ``host``, ``package``,
``repo``, ``rpm``, ``tag``, ``target``, ``task``, and ``user`` all
open the relevant koji web info page if a matching element could be
found.

The type ``tag-latest-dir`` accepts a tag as the argument, and will
open the tag's latest repository directory.

The type ``tag-repo-dir`` works similar to ``tag-latest-dir`` but
points to the actual repo ID path rather than the ``latest`` symlink.

The type ``build-dir`` accepts a build as the argument, and will open
the storage directory for that build's archives and logs.


References
----------

* :py:obj:`kojismokydingo.cli.clients.ClientOpen`
* :py:func:`kojismokydingo.cli.clients.cli_open`
