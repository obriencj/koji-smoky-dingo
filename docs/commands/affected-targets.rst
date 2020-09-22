koji affected-targets
=====================

.. highlight:: none

::

 usage: koji affected-targets [-h] [-q] [-i | -b] TAGNAME [TAGNAME ...]

 Show targets impacted by changes to the given tag(s)

 positional arguments:
   TAGNAME           Tag to check

 optional arguments:
   -h, --help        show this help message and exit
   -q, --quiet       Don't print summary information
   -i, --info        Print target name, build tag name, dest tag name
   -b, --build-tags  Print build tag names rather than target names


This command uses reversed tag inheritance to discover what targets
are inheriting (and are therefore affected by changes to) a given list
of tags.

When the ``--build-tags`` option is specified, then rather than
outputting a list of target names, the underlying build tag names are
displayed instead. This behavior is similar to ``koji
list-tag-inheritance --reverse`` but with additional filtering so that
only the child tags that are used in a target are displayed.

This can help an administrator to identify where the changes they make
may impact different target configurations -- ie. it helps to answer
the question "who will be having a bad day due to my changes to this
tag?"


References
----------

* :py:obj:`kojismokydingo.cli.tags.AffectedTargets`
* :py:func:`kojismokydingo.cli.tags.cli_affected_targets`
