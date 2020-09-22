koji unset-env-var
==================

.. highlight:: none

::

 usage: koji unset-env-var [-h] [--target] TAGNAME var

 Unset a mock environment variable on a tag

 positional arguments:
   TAGNAME     Name of tag
   var         Name of the environment variable

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


Note that the definition must have been set directly on the given tag,
and not inherited from a parent tag. There is currently no way to
block or undefine an inherited env var definition.

This command requires either the ``admin`` or ``tag`` permission,
as it modifies tag configuration data.

See also :ref:`koji list-env-vars`, :ref:`koji set-env-var`


References
----------

* :py:obj:`kojismokydingo.cli.tags.UnsetEnvVar`
* :py:func:`kojismokydingo.cli.tags.cli_unset_env_var`
