koji open
=========

.. highlight:: none

::

 usage: koji open [-h] [--command COMMAND] TYPE KEY

 Launch web UI for koji data elements

 positional arguments:
   TYPE                  The koji data element type. build, tag, target, user,
                         host, rpm, archive, task
   KEY                   The key for the given element type.

 optional arguments:
   -h, --help            show this help message and exit
   --command COMMAND, -c COMMAND
                         Command to exec with the discovered koji web URL

Launch local web browser to the informational page for a given koji data
element.


References
----------

* :py:obj:`kojismokydingo.cli.clients.ClientOpen`
* :py:func:`kojismokydingo.cli.clients.cli_open`
