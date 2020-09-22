koji userinfo
=============

.. highlight:: none

::

 usage: koji userinfo [-h] [--json] USER

 Show information about a user

 positional arguments:
   USER        User name or principal

 optional arguments:
   -h, --help  show this help message and exit
   --json      Output information as JSON


Display information about a user. Provides their status (enabled or
blocked), their type (user or group), their kerberos identities if
any, and a listing of any permissions they have. If the user is
configured to perform a CG import, this will also be presented.

For groups will also show the members.


References
----------

* :py:obj:`kojismokydingo.cli.users.UserInfo`
* :py:func:`kojismokydingo.cli.users.cli_userinfo`
* :py:func:`kojismokydingo.users.collect_userinfo`
