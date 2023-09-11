koji userinfo
=============

.. highlight:: none

::

 usage: koji userinfo [-h] [--stats] [--membership] [--json] USER

 Show information about a user or group

 positional arguments:
   USER        User name or principal

 options:
   -h, --help  show this help message and exit
   --stats     Include user statistics
   --membership
               Include group members or membership
   --json      Output information as JSON


Display information about a user or group. Provides their status
(enabled or blocked), their type (user or group), their kerberos
identities if any, and a listing of any permissions they have. If the
user is configured to perform CG imports, this will also be presented.

The ``--stats`` option was introduced in version 2.0.0, and provides
additional output:

* Owned package count
* Submitted task count
* Created builds count
* Last task summary
* Last build summary

Since version 2.2.0, this command will also show the list of members
if the specified user ID is actually a group


References
----------

* :py:obj:`kojismokydingo.cli.users.ShowUserInfo`
* :py:func:`kojismokydingo.cli.users.cli_userinfo`
* :py:func:`kojismokydingo.users.collect_userinfo`
* :py:func:`kojismokydingo.users.get_group_members`
