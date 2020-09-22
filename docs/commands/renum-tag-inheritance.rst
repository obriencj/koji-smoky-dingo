koji renum-tag-inheritance
==========================

.. highlight:: none

::

 usage: koji renum-tag-inheritance [-h] [--verbose] [--test] [--begin BEGIN]
                                   [--step STEP]
                                   TAGNAME

 Renumbers inheritance priorities of a tag, preserving order

 positional arguments:
   TAGNAME               Tag to renumber

 optional arguments:
   -h, --help            show this help message and exit
   --verbose, -v         Print information about what's changing
   --test, -t            Calculate the new priorities, but don't commit the
                         changes
   --begin BEGIN, -b BEGIN
                         New priority for first inheritance link (default: 10)
   --step STEP, -s STEP  Priority increment for each subsequent inheritance
                         link after the first (default: 10)


When you've been modifying a tag inheritance after repeated edits over
time, you may find that there's an insufficient gap between two
inherited parent priority values to fit another parent.

This command will adjust the priority values of a tag's immediate
parents such that they are in the same order, but are evenly spaced
out. Those familiar with Basic may recall the ``RENUM`` command.

This command requires either the ``admin`` or ``tag`` permission,
as it modifies tag configuration data.


References
----------

* :py:obj:`kojismokydingo.cli.tags.RenumTagInheritance`
* :py:func:`kojismokydingo.cli.tags.cli_renum_tag`
* :py:func:`kojismokydingo.tags.renum_inheritance`
