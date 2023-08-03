koji repoquery
==============

.. highlight:: none

::

 usage: koji repoquery [-h] [--target] [--arch ARCH] [--quiet | --queryformat QUERYFORMAT] [-C] [--cachedir CACHEDIR | --nocache]
                       [--file OWNSFILES] [--whatconflicts WHATCONFLICTS] [--whatdepends WHATDEPENDS] [--whatobsoletes WHATOBSOLETES]
                       [--whatprovides WHATPROVIDES] [--whatrequires WHATREQUIRES] [--whatrecommends WHATRECOMMENDS]
                       [--whatenhances WHATENHANCES] [--whatsuggests WHATSUGGESTS] [--whatsupplements WHATSUPPLEMENTS]
                       TAGNAME [KEY ...]

 Query the contents of a tag's repo

 positional arguments:
   TAGNAME               Name of tag

 options:
   -h, --help            show this help message and exit
   --target              Specify by target rather than a tag
   --arch ARCH           Select tag repo's architecture

 Output Options:
   --quiet, -q           Omit column headings
   --queryformat QUERYFORMAT
                         Output format for listing results

 Cache Options:
   -C, --cacheonly       Restrict to local cache if it exists
   --cachedir CACHEDIR   Override the default or configured cache directory
   --nocache             Use a temporary cache, removed after use

 Query Options:
   KEY                   The key(s) to search for
   --file OWNSFILES      Filter for packages containing these files
   --whatconflicts WHATCONFLICTS
                         Filter for packages with these Conflicts
   --whatdepends WHATDEPENDS
                         filter for packages with these Depends
   --whatobsoletes WHATOBSOLETES
                         filter for packages with these Obsoletes
   --whatprovides WHATPROVIDES
                         Filter for packages with these Provides
   --whatrequires WHATREQUIRES
                         Filter for packages with these Requires
   --whatrecommends WHATRECOMMENDS
                         filter for packages with these Recommends
   --whatenhances WHATENHANCES
                         filter for packages with these Enhances
   --whatsuggests WHATSUGGESTS
                         filter for packages with these Suggests
   --whatsupplements WHATSUPPLEMENTS
                         filter for packages with these Supplements


Performs an query on the current repository for a koji tag using
DNF. Correlates any matching RPM packages back to their owning koji
build and the inherited tag which holds that build.

This command can be used to assist in the debugging of dependencies in
a buildroot, allowing the user to easily identify where provides and
requires are being produced, and how those packages are being pulled
in.

This is similar to running dnf directly on the repository, but with
the added ability to perform build and tag correlation.

Introduced in version 2.1.0


Configuration
-------------

This command keeps a local repo cachedir by default. This value can be
overridden under the ``[repoquery]`` plugin configuration using the
setting named ``cachedir``

If the cachedir value is empty, then caches will be created in the
system temporary directory and purged immediately after each command.

eg. in ``~/.config/ksd/common.conf``

::

   [repoquery]
   # this is also the default value if left unspecified
   cachedir = ~/.cache/ksd/repoquery/


Command Availability
--------------------

This command relies on the dnf python package. However dnf is not
available as a standard wheel on PyPI. Instead, it is only made
available via system installs, typically on an RPM-managed Linux
distribution such as Fedora or Rocky Linux. Because of this, the
``koji repoquery`` command will dynamically make itself available only
when it detects that the relevant dependencies are present.

This can be an issue if the koji application is installed using a
different python version than dnf.

Warning: attempting to do a ``pip install dnf --user`` will leave an
intentionally broken ``dnf.py`` module in site-packages, which will
need to be removed to restore functionality.


Query Format
------------

In addition to the standard fields available to the ``--queryformat=``
option, this command also provides the fields of the correlating build
and tag. For example:

``--queryformat "%{tag.name} %{build.nvr} %{name}-%{evr}.%{arch}"``

This will output the name of the tag that the build was inherited
from, the NVR of the build, and then the RPM's name, evr, and
architecture.


References
----------

* :py:obj: `kojismokydingo.cli.tags.RepoQuery`
* :py:func: `kojismokydingo.cli.tags.cli_repoquery`
* `DNF, the next-generation replacement for YUM <https://dnf.readthedocs.io/en/latest/>`_
* `DNF Command Reference - Repoquery Command <https://dnf.readthedocs.io/en/latest/command_ref.html?highlight=repoquery#repoquery-command>`_
