koji list-env-vars
==================

.. highlight:: none

::

 usage: koji list-env-vars [-h] [--target]
                           [--quiet | --sh-declaration | --json]
                           TAGNAME

 Show mock environment variables for a tag

 positional arguments:
   TAGNAME               Name of tag

 optional arguments:
   -h, --help            show this help message and exit
   --target              Specify by target rather than a tag
   --quiet, -q           Omit headings
   --sh-declaration, -d  Output as sh variable declarations
   --json                Output as JSON


See also :ref:`koji set-env-var`, :ref:`koji unset-env-var`


References
----------

* :py:obj:`kojismokydingo.cli.tags.ListEnvVars`
* :py:func:`kojismokydingo.cli.tags.cli_list_env_vars`
