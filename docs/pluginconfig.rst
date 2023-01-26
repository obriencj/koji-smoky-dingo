Smoky Dingo Plugin Configuration
================================

.. highlight:: none

The koji configuration implementation is focused heavily on defining
koji profiles, and is therefore limited in what keys it will accept.
This makes it essentially impossible for a plugin to have its own
configuration unless it wants to define a separate config path and
loading system.

Koji Smoky Dingo assists in this space by providing an extensible
configuration system intended just for koji CLI plugins.


Configuration Format
--------------------

KSD plugin configuration is specified using the common config-file
format, as implemented in Python's `configparser.ConfigParser` API

Configuration files are loaded from two distinct directories. First
from a shared system directory, and then a user-specific directory.

These directories are discovered via the `AppDirs
<https://pypi.org/project/appdirs/>`_ package. Thus for example on a
linux system this will use the `XDG path specification
<https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_,
and so the system dir would likely be ``/etc/xdg/ksd/`` and the user
dir would be ``~/.local/config/ksd/``

From these two directories every file ending in the suffix ``.conf``
will be loaded in filename order. First all of the files from the
system dir, and then all of the files from the user dir. This ensures
that user configuration can override system configuration.

The individual config files are broken up into sections. These
sections are named after the plugin command whose configuration they
hold. For example, the configuration for ``koji pull-container`` would
be under a heading ``[pull-container]``

It is up to each plugin command to define the keys that they are
interesed in under their section. However, the ``enabled`` key is used
by the base SmokyDingo implementation by default. This key is used at
command loading time to determine whether the command should be
enabled or not. By default this setting is ``1`` meaning all commands
are used. However, setting ``enabled = 0`` will cause the meta plugin
to skip over that command, thus not adding it to the koji CLI.

For example, if a user wanted to disable the KSD version of the
``userinfo`` command in favor of the in-built command of the same name
in recent koji versions, they could have the following in a file named
``~/.local/config/ksd/common.conf``

::

   [userinfo]
   enable = 0


Configuration API
-----------------

Accessing plugin configurations is easiest via the method
`SmokyDingo.get_plugin_config
<kojismokydingo.cli.SmokyDingo.get_plugin_config>` which will
automatically load the configuration files and look for a section
matching the name of the instance of the command.

Outside of a SmokyDingo subclass, the `get_plugin_config
<kojismokydingo.common.get_plugin_config>` function offers the same
lookup, but the caller must specifcy the command or plugin's name.
