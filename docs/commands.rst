Plugin Commands
===============

Koji Smoky Dingo provides a number of additional commands to the
koji CLI.


Informational
-------------

These read-only commands gather and display information from Koji, and
do not require any special permissions to run.

.. toctree::
   :maxdepth: 1

   commands/affected-targets
   commands/cginfo
   commands/check-hosts
   commands/client-config
   commands/filter-builds
   commands/filter-tags
   commands/latest-archives
   commands/list-btypes
   commands/list-build-archives
   commands/list-cgs
   commands/list-component-builds
   commands/list-env-vars
   commands/list-rpm-macros
   commands/list-tag-extras
   commands/open
   commands/perminfo
   commands/userinfo


Administrative
--------------

These commands modify aspects of Koji and are subsequently gated
behind some level of administrative permission.

See `Koji's Permission System - Administration <https://docs.pagure.org/koji/permissions/#administration>`_

.. toctree::
   :maxdepth: 1

   commands/block-env-var
   commands/block-rpm-macro
   commands/bulk-tag-builds
   commands/remove-env-var
   commands/remove-rpm-macro
   commands/renum-tag-inheritance
   commands/set-env-var
   commands/set-rpm-macro
   commands/swap-tag-inheritance


.. toctree::
   :hidden:

   commands/unset-env-var
   commands/unset-rpm-macro
