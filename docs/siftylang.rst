Sifty Dingo Filtering Language
==============================

The `kojismokydingo.sift` package implements a minimal filtering
language tentatively named "sifty dingo". The language is based on
predicates written as a sequence of s-expressions.


Language Example
----------------
::

  (flag inactive (!status ACTIVE))
  (flag old-guard (not (inactive?)) (joined-before 2000-01-01))
  (flag noob (not (inactive?)) (joined-after 2020-01-01))
  (!flagged noob old-guard inactive)

This example presumes three predicates have been created;
``joined-after``, ``joined-before``, and ``status``. Each of these
take a single argument at their initialization.

When a `Sifter` is compiled from the above source, it will contain
four `Sieve` rules. When that sifter instance is invoked on a set of
data, each of the four rules will be invoked in order. The first three
rules will set their relevant flags on any data entries which matched
their predicates. The fourth rule has no explicit flag, and so its
results would be implicitly flagged with "default"

Loosely translated, this example means:

  * flag as inactive anyone whose status is not ACTIVE
  * flag as old-guard anyone that isn't flagged inactive and whose
    joined-before predicate is true for the value 2000-01-01
  * flag as a noob anyone that isn't flagged inactive and whose
    joined-after predicate is true for the value 2020-10-01
  * flag as default anyone what doesn't have the noob, old-guard,
    nor inactive flags


Built-In Sieve Expressions
--------------------------

The language supports three logical expressions; ``and``, ``or``, and
``not``. Each of these apply a logical constraint on top of other
expressions.


Logical Expression ``and``
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  (and EXPR [EXPR...])

Matches data items which pass through all of the sub-expressions. Once
a data item fails to match, it will not be passed along to further
sub-expressions.


Logical Expression ``or``
^^^^^^^^^^^^^^^^^^^^^^^^^
::

  (or EXPR [EXPR...])

Matches data items which pass through any of the sub-expressions. Once
a data item has been matched, it will not be passed along to further
sub-expressions.


Logical Expression ``not``
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  (not EXPR [EXPR...])

Matches data items which pass none of the sub-expressions. Once a data item
has been matched, it will not be passed along to further sub-expressions.

As a convenience, ``!`` is a synonym for ``not``.

Any expression can be inverted by prefixing it with ``!`` or
``not-``. For example, all of these are equivalent expressions:

  * ``(not (foo 1))``
  * ``(not-foo 1)``
  * ``(! (foo 1))``
  * ``(!foo 1)``


Expression ``flag``
^^^^^^^^^^^^^^^^^^^
::

  (flag NAME EXPR [EXPR...])

Acts like the ``and`` logical expression. In addition to passing its
matches, this expression will also set the given flag name on each
data item that matched all sub-expressions.


Predicate ``flagged``
^^^^^^^^^^^^^^^^^^^^^
::

  (flagged NAME [NAME...])

Matches data items which have had any of the named flags applied to it
previously.

As a convenience, ``?`` is a synonym for ``flagged``.

In addition, any flag can be used as its own predicate by appending a
``?`` to its name. For example, the following are equivalent expressions:

  * ``(flagged awesome)``
  * ``(? awesome)``
  * ``(awesome?)``
