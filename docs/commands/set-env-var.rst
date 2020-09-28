koji set-env-var
================

.. highlight:: none

::

 usage: koji set-env-var [-h] [--remove] [--block] [--target]
                         TAGNAME var [value]

 Set a mock environment variable on a tag

 positional arguments:
   TAGNAME     Name of tag
   var         Name of the environment variable
   value       Value of the environment var. Default: ''

 optional arguments:
   -h, --help  show this help message and exit
   --remove    Remove the environment var from the tag
   --block     Block the environment var from the tag
   --target    Specify by target rather than a tag


This command requires either the ``admin`` or ``tag`` permission,
as it modifies tag configuration data.

See also :ref:`koji list-env-vars`


References
----------

* :py:obj:`kojismokydingo.cli.tags.SetEnvVar`
* :py:func:`kojismokydingo.cli.tags.cli_set_env_var`
