koji remove-env-var
===================

.. highlight:: none

::

 usage: koji remove-env-var [-h] [--target] TAGNAME var

 Remove a mock environment variable from a tag

 positional arguments:
   TAGNAME     Name of tag
   var         Name of the environment variable

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


This command is a convenience equivalent to ``koji set-env-var --remove``

See also :ref:`koji list-env-vars`, :ref:`koji set-env-var`, :ref:`koji block-env-var`


References
----------

* :py:obj:`kojismokydingo.cli.tags.RemoveEnvVar`
* :py:func:`kojismokydingo.cli.tags.cli_set_env_var`
