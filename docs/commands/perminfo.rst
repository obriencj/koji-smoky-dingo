koji perminfo
=============

.. highlight:: none

::

 usage: koji perminfo [-h] [--verbose] [--by-date] [--json] PERMISSION

 Show information about a permission

 positional arguments:
   PERMISSION     Name of permission

 optional arguments:
   -h, --help     show this help message and exit
   --verbose, -v  Also show who granted the permission and when
   --by-date, -d  Sory users by date granted. Otherwise, sort by name
   --json         Output information as JSON


Provides information about a permission, including which users are
granted it. When ``--verbose`` mode is enabled, will also indicate
what user granted the permission to them, and when.


References
----------

* :py:obj:`kojismokydingo.cli.users.PermissionInfo`
* :py:func:`kojismokydingo.cli.users.cli_perminfo`
* :py:func:`kojismokydingo.users.collect_perminfo`
