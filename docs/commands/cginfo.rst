koji cginfo
===========

.. highlight:: none

::

 usage: koji cginfo [-h] [--name NAME] [--json]

 List content generators and their users

 optional arguments:
   -h, --help   show this help message and exit
   --name NAME  Only show the given content generator
   --json       Output information as JSON


This command will display the names of content generators that have
been registered with the given koji instance. It will also list the
user accounts which have been granted permission to perform cg-imports
on behalf of that content generator.


References
----------

* :py:obj:`kojismokydingo.cli.users.CGInfo`
* :py:func:`kojismokydingo.cli.users.cli_cginfo`
