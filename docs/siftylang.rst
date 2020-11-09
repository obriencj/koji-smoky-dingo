Sifty Dingo Filtering Language
==============================

The `kojismokydingo.sift` package implements a minimal filtering
language tentatively named "sifty dingo". The language is based on
predicates written as a sequence of s-expressions.


Language Example
----------------
.. highlight:: none

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


Literal Types
-------------

The language is composed of a series of nested sieve predicates, each
with a symbol as its first element denoting the name of the
sieve. Subsequent elements are the arguments to the predicate.


Literal Sieve
^^^^^^^^^^^^^
.. highlight:: none

  (foo)
  (foo 1 two "three" /four/ |five|)
  (and (foo 1) (bar 2))
  (or (baz 3) (and (qux) (quux 4)))

A sieve predicate bears the form of an S-Expression, with opening and
closing parenthesis characters denoting the contents. The first
element is the name of the predicate.

Sieve predicates are not used to evalute to a value -- they are
True/False tests which are applied to the data which is fed to the
fully compiled sifter. Because of this, it is rare that they are
nested except in the case of the logical combining predicates.


Literal Symbol
^^^^^^^^^^^^^^
.. highlight:: none

   foo
   Tacos-and-Pizza
   1.2.34

Symbols are unquoted alphanumerics. They are white-space terminated.
Symbols are used to resolve the class of a predicate. Symbols are a
valid matching type, which function similarly to a string. A symbol
cannot be entirely numeric -- it would instead be interpreted as a
Number in that case.


Literal Number
^^^^^^^^^^^^^^
.. highlight:: none

   123
   002

Numbers are unquoted numerics. They can be compared with both integer
values and strings.


Literal Symbol Group
^^^^^^^^^^^^^^^^^^^^
.. highlight:: none

   foo-{001..005}
   {foo,bar}-001
   {hello,goodbye}-{cruel,happy}-world
   109{2,4,5}1
   10{002..106..2}

A Symbol Group is an entity which represents a collection of symbols
based on some substitutions. Substitutions are bounded in matching
``'{'`` and ``'}'`` characters. Substitutions may be either a
comma-separated list of values, or a double-dotted range. A Symbol
Group matches any string value that is represented by the product of
its substitutions.

If a Symbol Group is entirely numeric, it will match with rules
similar to Number.

If any part of a substitution is malformed, that substitution will be
treated as a single symbol value. If a Symbol Group contains only one
possible product, it will become a simple Symbol.


Literal Regex
^^^^^^^^^^^^^
.. highlight:: none

   /^Foo.*Bar$/
   /^FOO.*BAR$/i

A Regex is quoted with matching ``'/'`` characters. Optional flags
can be appendes to the regex by specifying the characters immediately
after the closing ``'/'``


Literal Globs
^^^^^^^^^^^^^
.. highlight:: none

   |foo*|
   |FOO*|i

A Glob is quoted with matching ``'|'`` characters. An optional
trailing ``'i'`` can be used to indicate the glob matching is
case-insensitive.


Literal Item Path
^^^^^^^^^^^^^^^^^
.. highlight:: none

   .foo
   .bar[].qux
   [2::1].baz[{ping,pong}]

An item path is a way to select elements of the given data objects for
matching.

Item paths can be used as the first argument to the built-in ``item``
predicate.

Using an item path as the first element in a sieve is also a shortcut
for invoking the ``item`` predicate. These are equivalent expressions:

  * ``(.foo {100..200})``
  * ``(item .foo {100..200})``


Built-In Sieve Predicates
-------------------------

The language supports three logical expressions; ``and``, ``or``, and
``not``. Each of these apply a logical constraint on top of other
expressions. The language also provides a way to set flags via tha
``flag`` expression, and to check flags via the ``flagged`` predicate.
There final built-in predicate is ``item`` which is used to do value
comparisons against the data structures themselves.


Logical Predicate ``and``
^^^^^^^^^^^^^^^^^^^^^^^^^
.. highlight:: none

  (and EXPR [EXPR...])

Matches data items which pass through all of the sub-expressions. Once
a data item fails to match, it will not be passed along to further
sub-expressions.


Logical Predicate ``or``
^^^^^^^^^^^^^^^^^^^^^^^^
.. highlight:: none

  (or EXPR [EXPR...])

Matches data items which pass through any of the sub-expressions. Once
a data item has been matched, it will not be passed along to further
sub-expressions.


Logical Predicate ``not``
^^^^^^^^^^^^^^^^^^^^^^^^^
.. highlight:: none

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
.. highlight:: none

  (flag NAME EXPR [EXPR...])

Acts like the ``and`` logical expression. In addition to passing its
matches, this expression will also set the given flag name on each
data item that matched all sub-expressions.


Predicate ``flagged``
^^^^^^^^^^^^^^^^^^^^^
.. highlight:: none

  (flagged NAME [NAME...])

Matches data items which have had any of the named flags applied to it
previously.

As a convenience, ``?`` is a synonym for ``flagged``.

In addition, any flag can be used as its own predicate by appending a
``?`` to its name. For example, the following are equivalent expressions:

  * ``(flagged awesome)``
  * ``(? awesome)``
  * ``(awesome?)``


Predicate ``item``
^^^^^^^^^^^^^^^^^^
.. highlight:: none

   (item PATH [VALUE...])

Resolves an `ItemPath` against each data item. If any values are supplied as
an argument, then the predicate will pass any data items which has any path
element that matches to any of the values. If no values are supplied then
the path elements simply need to be present and non-null.
