Sifty Dingo Filtering Language
==============================

.. highlight:: none

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


Basic Syntax
------------

The language is composed of a series of nested sieve predicates, each
with a symbol as its first element denoting the name of the
sieve. Subsequent elements are the arguments to the predicate.


Sieve Predicate
^^^^^^^^^^^^^^^
::

  (foo)
  (foo 1 two "three" /four/ |five|)
  (and (foo 1) (bar 2))
  (or (baz 3) (and (qux) (quux 4)))

A sieve predicate bears the form of an S-Expression, with opening and
closing parenthesis characters denoting the contents. The first
element identifies the name of the predicate.

Sieve predicates are not used to evalute to a value -- they are
True/False tests which are applied to the data which is fed to the
fully compiled sifter. Because of this, it is rare that they are
nested except in the case of the logical combining predicates.


Symbol
^^^^^^
::

   foo
   Tacos-and-Pizza
   1.2.34

Symbols are unquoted alphanumerics. They are white-space terminated.
Symbols are used to resolve the class of a predicate when they are the
first element of a sieve. Symbols are also a valid matching type, and
they function similarly to a string. A symbol cannot be entirely
numeric -- it would instead be interpreted as a Number in that case.

Symbols with a leading dollar-sign are interpreted as variables, and
their value will be substituted from a sifter parameter at compile
time.


Number
^^^^^^
::

   123
   002
   -1

Numbers are unquoted series of digits, with an optional leading
negative sign. They can be compared with both integer and string
values.


Symbol Group
^^^^^^^^^^^^
::

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


String
^^^^^^^
::

   "Foo bar"

A string is quoted with matching ``'"'`` characters. Normal escape
sequences are honored.

Strings may interpolate variables from the sifter at compile time
using Python's `str.format` markup rules.


Regex
^^^^^
::

   /^Foo.*Bar$/
   /^FOO.*BAR$/i

A Regex is quoted with matching ``'/'`` characters. Optional flags
can be appendes to the regex by specifying the characters immediately
after the closing ``'/'``


Glob
^^^^
::

   |foo*|
   |FOO*|i

A Glob is quoted with matching ``'|'`` characters. An optional
trailing ``'i'`` can be used to indicate the glob matching is
case-insensitive.


Item Path
^^^^^^^^^
::

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


Core Sieves
-----------

The language supports three logical expressions; ``and``, ``or``, and
``not``. Each of these apply a logical constraint on top of other
expressions. The language also provides a way to set flags via tha
``flag`` expression, and to check flags via the ``flagged`` predicate.
There final built-in predicate is ``item`` which is used to do value
comparisons against the data structures themselves.


Statement ``flag``
^^^^^^^^^^^^^^^^^^
::

  (flag NAME EXPR [EXPR...])

Acts like the ``and`` logical expression. In addition to passing its
matches, this expression will also set the given flag name on each
data item that matched all sub-expressions.


Logical ``and``
^^^^^^^^^^^^^^^
::

  (and EXPR [EXPR...])

Matches data items which pass through all of the sub-expressions. Once
a data item fails to match, it will not be passed along to further
sub-expressions.


Logical ``or``
^^^^^^^^^^^^^^
::

  (or EXPR [EXPR...])

Matches data items which pass through any of the sub-expressions. Once
a data item has been matched, it will not be passed along to further
sub-expressions.


Logical ``not``
^^^^^^^^^^^^^^^
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


Predicate ``flagged``
^^^^^^^^^^^^^^^^^^^^^
::

  (flagged NAME [NAME...])

Matches data items which have had any of the named flags applied to it
previously.

As a convenience, ``?`` is a synonym for ``flagged``.

In addition, any flag can be used as its own predicate by appending a
``?`` to its name. For example, the following are equivalent:

  * ``(flagged awesome)``
  * ``(? awesome)``
  * ``(awesome?)``


Predicate ``item``
^^^^^^^^^^^^^^^^^^
::

   (item PATH [VALUE...])

Resolves an `ItemPath` against each data item. If any values are supplied as
an argument, then the predicate will pass any data items which has any path
element that matches to any of the values. If no values are supplied then
the path elements simply need to be present and non-null.

The item predicate may be specified implicitly by making the first element
of the sieve an ItemPath. For example, the following are equivalent:

  * ``(item .foo[].bar {1..100})``
  * ``(.foo[].bar {1..100})``


Build Sieves
------------

To facilitate filtering sequences of koji build info dicts, there are
a number of available sieves provided in the
`kojismokydingo.sift.builds` module.

A sifter instance with these and the core sieves available by default can be
created via :py:func:`kojismokydingo.sift.builds.build_info_sifter`


Build EVR Comparison Predicates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (OP VER)

``OP`` can be any of the following comparison operators:

  * ``==``
  * ``!=``
  * ``>``
  * ``>=``
  * ``<``
  * ``<=``

``VER`` can be in any of the following forms:

  * ``EPOCH:VERSION``
  * ``EPOCH:VERSION-RELEASE``
  * ``VERSION``
  * ``VERSION-RELEASE``

If ``EPOCH`` is omitted, it is presumed to be ``0``.
If ``RELEASE`` is omitted, it is presumed to be equivalent.

These predicates filter by using RPM EVR comparison rules against the
epoch, version, and release values of the builds.


Build Predicate ``cg-imported``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (cg-imported [CGNAME...])

Filters for builds which were produced by a koji Content Generator via
the ``CGImport`` API. Such builds would have no task ID associated
with them.

If any optional ``CGNAME`` matchers are supplied, then filters for
builds which are produced by matching content generators only.


Build Predicate ``compare-latest-id``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (compare-latest-id OP TAG)

Filters for builds which have an ID that compares to the latest build
of the same package name in the given tag. If there is no matching
build in the tag, then the filtered build will not be included.

``OP`` can be any of the following comparison operators: ``==``,
``!=``, ``>``, ``>=``, ``<``, ``<=``

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``compare-latest-nvr``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (compare-latest-nvr OP TAG)

Filters for builds which have an NVR that compares to the latest build
of the same package name in the given tag. If there is no matching
build in the tag, then the filtered build will not be included.

``OP`` can be any of the following comparison operators: ``==``,
``!=``, ``>``, ``>=``, ``<``, ``<=``

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``epoch``
^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (epoch EPOCH [EPOCH...])

Filters for builds whose epoch value matches any of the given ``EPOCH``
patterns.


Build Predicate ``imported``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (imported)

Filters for builds which have no task ID. These builds could be either raw
imports or from a content generator.


Build Predicate ``inherited``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (inherited TAG [TAG...])

Filters for builds which are tagged in any of the given ``TAG`` or
their parents.

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``latest``
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (latest TAG [TAG...])

Filters for builds which are the latest of their package name in any
of the given ``TAG``, following inheritance and honoring package
listings and blocks.

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``latest-maven``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (latest-maven TAG [TAG...])

Filters for maven builds which are the latest of their GAV (group,
artifact, version) in any of the given ``TAG``, following inheritance
and honoring package listings and blocks.

This differs from the ``latest`` predicate in that multiple copies of
the same package may be considered the latest using this method. The
uniqueness is by the GAV rather than the package name.

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``name``
^^^^^^^^^^^^^^^^^^^^^^^^
::

   (name NAME [NAME...])

Filters for builds which have a name matching any of the given
``NAME`` patterns.


Build Predicate ``nvr``
^^^^^^^^^^^^^^^^^^^^^^^
::

   (nvr NVR [NVR...])

Filters for builds which have an NVR matching any of the given ``NVR``
(name-version-release) patterns.


Build Predicate ``owner``
^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (owner USER [USER...])

Filters for builds whose owner's name or ID matches any of the given
``USER``. ``USER`` may be specified by either name or ID, but not by
pattern. ``USER`` will be validated when the sieve is first run --
this may result in a `kojismokydingo.NoSuchUser` exception being
raised.


Build Predicate ``pkg-allowed``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (pkg-allowed TAG [TAG...])

Filters for builds whose package name is allowed in any of the given
tags, honoring inheritance.

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``pkg-blocked``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (pkg-blocked TAG [TAG...])

Filters for builds whose package name is explicitly blocked in any of
the given tags, honoring inheritance.

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``pkg-unlisted``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (pkg-unlisted TAG [TAG...])

Filters for builds which have their package name unlisted (neither
allowed nor blocked) in any of the given tags, honoring inheritance.

``TAG`` may be specified by either name or ID, but not by pattern.
``TAG`` will be validated when the sieve is first run -- this may
result in a `kojismokydingo.NoSuchTag` exception being raised.


Build Predicate ``release``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (release REL [REL...])

Filters for builds which have a release matching any of the given
``REL`` patterns.


Build Predicate ``signed``
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (signed [SIGKEY...])

Filters for builds which have an RPM archive that has been signed with
a key matching any of the given ``SIGKEY`` patterns.

If no ``SIGKEY`` patterns are supplied, then filters for builds which
have an RPM archive that has been signed with any key.


Build Predicate ``state``
^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (state STATE [STATE...])

Filters for builds which are in one of the given build states. Each
``STATE`` may be specified as either a name or a state ID, but each
must be a valid koji build state.

Valid states are:

  * ``1`` ``BUILDING``
  * ``2`` ``COMPLETE``
  * ``3`` ``DELETED``
  * ``4`` ``FAILED``
  * ``5`` ``CANCELED``


Build Predicate ``tagged``
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (tagged [TAG...])

Filters for builds which are tagged with a tag having a name or ID
matching any of the given ``TAG`` patterns.

If no ``TAG`` patterns are specified, then filters for builds which
have any tags at all.


Build Predicate ``type``
^^^^^^^^^^^^^^^^^^^^^^^^
::

   (type BTYPE [BTYPE...])

Filters for builds which have archives of the given build type. Normal
build types are rpm, maven, image, and win. Koji instances may support
plugins which extend the available build types beyond these.


Build Predicate ``version``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (version VER [VER...])

Filters for builds which have a version matching any of the given
``VER`` patterns.


Tag Sieves
----------

To facilitate filtering sequences of koji tag info dicts, there are
a number of available sieves provided in the
`kojismokydingo.sift.tags` module.

A sifter instance with these and the core sieves available by default can be
created via :py:func:`kojismokydingo.sift.tags.tag_info_sifter`


Tag Predicate ``all-group-pkg``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (all-group-pkg GROUP PKG [PKG...])

Matches tags which have the given install group, which must also
contain all of the given ``PKG`` names


Tag Predicate ``arch``
^^^^^^^^^^^^^^^^^^^^^^
::

   (arch [ARCH...])

If no ``ARCH`` patterns are specified, matches tags which have any
architectures at all.

If ``ARCH`` patterns are specified, then only matches tags which have
an architecture that matches any of the given patterns.


Tag Predicate ``build-tag``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (build-tag [TARGET...])

If no ``TARGET`` is specified, then matches tags which are used as the
build tag for any target.

If any ``TARGET`` patterns are specified, then matches tags which are
used as the build tag for a target with a name matching any of the
patterns.


Tag Predicate ``compare-latest``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (compare-latest PACKAGE [OP VERSION])

If ``OP`` and ``VERSION`` are not specified, matches tags which have
any build of the given ``PACKAGE`` name as latest.

If ``OP`` and ``VERSION`` are specified, matches tags which have the a
latest build of the given ``PACKAGE`` name which compare correctly. If
tag doesn't have any build of the given package, it will not match.

``OP`` can be any of the following comparison operators: ``==``,
``!=``, ``>``, ``>=``, ``<``, ``<=``

``VERSION`` can be in any of the following forms:

  * ``EPOCH:VERSION``
  * ``EPOCH:VERSION-RELEASE``
  * ``VERSION``
  * ``VERSION-RELEASE``

If ``EPOCH`` is omitted, it is presumed to be ``0``.
If ``RELEASE`` is omitted, it is presumed to be equivalent.


Tag Predicate ``dest-tag``
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (dest-tag [TARGET...])

If no ``TARGET`` is specified, then matches tags which are used as the
destination tag for any target.

If any ``TARGET`` patterns are specified, then matches tags which are
used as the destination tag for a target with a name matching any of
the patterns.


Tag Predicate ``exact-arch``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (exact-arch [ARCH...])

If no ``ARCH`` names are specified, matches only tags which have no
architectures.

If ``ARCH`` names are specified, they must be specified as
symbols. Only matches tags which have the exact same set of
architectures.


Tag Predicate ``group``
^^^^^^^^^^^^^^^^^^^^^^^
::
   (group GROUP [GROUP...])

Matches tags which have any of the given install groups configured.
Honors inheritance.


Tag Predicate ``group-pkg``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
   (group-pkg GROUP PKG [PKG...])

Matches tags which have the given install group, which also contains
any of the given ``PKG`` names


Tag Predicate ``has-ancestor``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (has-ancestor [TAG...])
   (inherits-from [TAG...])

If no ``TAG`` patterns are specified, matches tags which have any
parents.

If ``TAG`` patterns are specified, matches tags which have a parent at
any depth matching any of the given patterns.


Tag Predicate ``has-child``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (has-child [TAG...])
   (parent-of [TAG...])

If no ``TAG`` patterns are specified, matches tags which are the
direct parent to any other tag.

If ``TAG`` patterns are specified, matches tags which are the direct
parent to any tag matching any of the given patterns.


Tag Predicate ``has-descendant``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (has-descendant [TAG...])
   (inherited-by [TAG...])

If no ``TAG`` patterns are specified, matches tags which are inherited
by any other tag.

If ``TAG`` patterns are specified, matches tags which are inherited by
any tag matching any of the patterns, at any depth.


Tag Predicate ``has-parent``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (has-parent [TAG...])
   (child-of [TAG...])

If no ``TAG`` patterns are specified, matches tags which have any
parents.

If ``TAG`` patterns are specified, matchs tags which have any direct
parent matching any of the given patterns.


Tag Predicate ``locked``
^^^^^^^^^^^^^^^^^^^^^^^^
::

   (locked)

Matches tags which have been locked.


Tag Predicate ``name``
^^^^^^^^^^^^^^^^^^^^^^
::

   (name NAME [NAME...])

Matches tags which have a name that matches any of the given ``NAME``
patterns.


Tag Predicate ``permission``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (permission [PERM...])

If no ``PERM`` is specified, then matches tags which have any
permission set.

If any ``PERM`` patters are specified, then matches tags which have
any of the listed permissions set.


Tag Predicate ``pkg-allowed``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (pkg-allowed PKG [PKG...])

Matches tags which have a package listing with any of the given
``PKG`` contained therein and not blocked, honoring inheritance.


Tag Predicate ``pkg-blocked``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (pkg-blocked PKG [PKG...])

Matches tags which have a package listing with any of the given
``PKG`` contained therein and blocked, honoring inheritance.


Tag Predicate ``pkg-unlisted``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

   (pkg-unlisted PKG [PKG...])

Matches tags which have no package listing (neither allowed nor
blocked) for any of the given ``PKG`` names. Honors inheritance.
