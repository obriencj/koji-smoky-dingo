koji block-env-var
==================

.. highlight:: none

::

 usage: koji block-env-var [-h] [--target] TAGNAME var

 Block a mock environment variable from a tag

 positional arguments:
   TAGNAME     Name of tag
   var         Name of the environment variable

 optional arguments:
   -h, --help  show this help message and exit
   --target    Specify by target rather than a tag


This command is a convenience equivalent to ``koji set-env-var --block``

See also :ref:`koji list-env-vars`, :ref:`koji set-env-var`, :ref:`koji remove-env-var`


References
----------

* :py:obj:`kojismokydingo.cli.tags.BlockEnvVar`
* :py:func:`kojismokydingo.cli.tags.cli_set_env_var`
