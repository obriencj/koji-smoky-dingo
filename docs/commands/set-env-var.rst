koji set-env-var
================

.. highlight:: none

::

 usage: koji set-env-var [-h] [--target] TAGNAME var [value]

 Set a mock environment variable on a tag

 positional arguments:
   TAGNAME     Name of tag
   var         Name of the environment variable
   value       Value of the environment var. Default: ''

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


This permission requires either the ``admin`` or ``tag`` permission,
as it modifies tag configuration data.

See also :ref:`koji list-env-vars`, :ref:`koji unset-env-var`


References
----------

* :py:obj:`kojismokydingo.cli.tags.SetEnvVar`
* :py:func:`kojismokydingo.cli.tags.cli_set_env_var`
