koji client-config
==================

.. highlight:: none

::

 usage: koji client-config [-h] [--quiet | --json | --cfg]
                           [SETTING [SETTING ...]]

 Show client profile settings

 positional arguments:
   SETTING      Limit to these settings (default: all settings)

 optional arguments:
   -h, --help   show this help message and exit
   --quiet, -q  Do not print setting keys
   --json       Output settings as JSON
   --cfg        Output settings as a config file


Easily fetch information from the local client config for a given koji
profile on the command line.

The profile settings can be output as either a colon-separated
mapping, a configfile compatible ini format, or json.

This command also allows fetching individual settings, which may be
useful when working with additional layers of bash scripting.


References
----------

* :py:obj:`kojismokydingo.cli.clients.ClientConfig`
* :py:func:`kojismokydingo.cli.clients.cli_client_config`
