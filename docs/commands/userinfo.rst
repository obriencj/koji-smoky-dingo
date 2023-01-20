koji userinfo
=============

.. highlight:: none

::

 usage: koji userinfo [-h] [--stats] [--json] USER

 Show information about a user

 positional arguments:
   USER        User name or principal

 options:
   -h, --help  show this help message and exit
   --stats     Include user statistics
   --json      Output information as JSON


Display information about a user. Provides their status (enabled or
blocked), their type (user or group), their kerberos identities if
any, and a listing of any permissions they have. If the user is
configured to perform a CG import, this will also be presented.

User statistics include
* Owned package count
* Submitted task count
* Created builds count
* Last task summary
* Last build summary

For groups this command will also show the members.


References
----------

* :py:obj:`kojismokydingo.cli.users.UserInfo`
* :py:func:`kojismokydingo.cli.users.cli_userinfo`
* :py:func:`kojismokydingo.users.collect_userinfo`
