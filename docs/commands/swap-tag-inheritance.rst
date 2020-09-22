koji swap-tag-inheritance
=========================

.. highlight:: none

::

 usage: koji swap-tag-inheritance [-h] [--verbose] [--test]
                                  TAGNAME OLD_PARENT_TAG NEW_PARENT_TAG

 Swap a tag's inheritance

 positional arguments:
   TAGNAME         Name of tag to modify
   OLD_PARENT_TAG  Old parent tag's name
   NEW_PARENT_TAG  New parent tag's name

 optional arguments:
   -h, --help      show this help message and exit
   --verbose, -v   Print information about what's changing
   --test, -t      Calculate the new inheritance, but don't commit the changes.


Swaps the parent inheritence of a tag.

If the new and old parents are both already in the direct inheritance
of the tag, then their priorities will be swapped.

If the new parent is not already in the direct inheritance of the tag,
then the old parent will be removed and new parent will be set in its
place at the same priority.


References
----------

* :py:obj:`kojismokydingo.cli.tags.SwapTagInheritance`
* :py:func:`kojismokydingo.cli.tags.cli_swap_inheritance`
