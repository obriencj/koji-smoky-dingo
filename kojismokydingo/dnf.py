# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


"""
Koji Smoky Dingo - DNF ease-of-use wrappers

:since: 2.1

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from contextlib import contextmanager
from functools import wraps
from itertools import cycle, repeat
from koji import ClientSession
from os.path import abspath
from re import compile as compile_re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any, Callable, Generator, List, Optional, Tuple

from . import BadDingo, bulk_load_builds
from .types import BuildInfo, TagInfo, TypedDict


try:
    from typing import TypeAlias  # type: ignore
except ImportError:
    from typing_extensions import TypeAlias


# this tomfoolery is to work around situations where we want to use
# mypy on a system where dnf is not available

BaseType: TypeAlias
MainConfType: TypeAlias
PackageType: TypeAlias
QueryType: TypeAlias
SackType: TypeAlias


try:
    from dnf.base import Base
    from dnf.conf import Conf
    from dnf.conf.config import MainConf
    from dnf.i18n import ucd
    from dnf.package import Package
    from dnf.query import Query
    from dnf.sack import Sack
    from dnf.subject import Subject
    from dnf.util import ensure_dir

except ImportError:
    __ENABLED = False

    BaseType = "dnf.base.Base"
    MainConfType = "dnf.conf.Conf"
    PackageType = "dnf.package.Package"
    QueryType = "dnf.query.Query"
    SackType = "dnf.sack.Sack"

else:
    __ENABLED = True

    BaseType = Base
    MainConfType = Conf
    PackageType = Package
    QueryType = Query
    SackType = Sack


__all__ = (
    "DNFuq",
    "DNFUnavailable",
    "correlate_query_builds",
    "dnf_available",
    "dnf_config",
    "dnf_sack",
    "dnfuq",
    "dnfuq_formatter",
)


class DNFuqFilterTerms(TypedDict):
    ownsfiles: Optional[List[str]]
    whatconflicts: Optional[List[str]]
    whatdepends: Optional[List[str]]
    whatobsoletes: Optional[List[str]]
    whatprovides: Optional[List[str]]
    whatrequires: Optional[List[str]]
    whatrecommends: Optional[List[str]]
    whatenhances: Optional[List[str]]
    whatsuggests: Optional[List[str]]
    whatsupplements: Optional[List[str]]


DNFUQ_FILTER_TERMS = (
    "ownsfiles", "whatconflicts", "whatdepends",
    "whatobsoletes", "whatprovides", "whatrequires",
    "whatrecommends", "whatenhances",
    "whatsuggests", "whatsupplements", )


class DNFUnavailable(BadDingo):
    complaint = "dnf package unavailable"


def dnf_available():
    """
    True if the dnf package and assorted internals could be
    successfully imported. False otherwise.
    """

    return __ENABLED


def requires_dnf(fn):
    @wraps(fn)
    def wrapper(*args, **kwds):
        if not __ENABLED:
            raise DNFUnavailable(f"API call {fn.__name__} requires dnf")
        return fn(*args, **kwds)
    return wrapper


@requires_dnf
def dnf_config(
        cachedir: str,
        arch: str = None) -> MainConfType:
    """
    produces a dnf main configuration appropriate for use outside
    of managing a local system

    :param cachedir: the base directory to create per-repository
      caches in.

    :param arch: override the architecture. By default the local
      system architecture is used.

    :raises DNFUnavailable: if the dnf module is not available

    :raises ValueError: if cachedir is not suppled

    :since: 2.1
    """

    if not cachedir:
        raise ValueError("cannot execute query without a cachedir")

    ensure_dir(cachedir)

    mc = MainConf()
    mc.cachedir = cachedir

    if arch:
        mc.arch = arch

    return mc


@requires_dnf
def dnf_sack(config: MainConfType,
             path: str,
             label: str = "koji") -> SackType:

    """
    Creates a dnf sack with a single repository, in order for
    queries to be created against that repo.

    :param config: a dnf main configuration

    :param path: repository path

    :param label: repository label. This will be used to determine the
      specific caching directory

    :raises DNFUnavailable: if the dnf module is not availaable

    :since: 2.1
    """

    if "://" not in path:
        path = "file://" + abspath(path)

    base = Base(config)
    base.repos.add_new_repo(label, config, baseurl=[path])

    base._sack = Sack(pkgcls=Package, pkginitval=base,
                      arch=config.substitutions["arch"],
                      cachedir=config.cachedir, logdebug=False)

    base._add_repo_to_sack(base.repos[label])

    return base.sack


@contextmanager
@requires_dnf
def dnfuq(path: str,
          label: str = "koji",
          arch: str = None,
          cachedir: str = None) -> Generator["DNFuq", None, None]:

    """
    context manager providing a DNFuq instance configured with
    either a re-usable or temporary cache directory.

    :param path: path to the repository

    :param label: repository label, for use in storing the repository
      cache

    :param arch: override the architecture. By default the local
      system architecture is used.

    :param cachedir: the base directory for storing repository
      caches. If omitted the system temp directory will be used, and
      the cache will be deleted afterwards.

    :raises DNFUnavailable: if the dnf module is not available

    :since: 2.1
    """

    if cachedir:
        yield DNFuq(path, label=label, arch=arch, cachedir=cachedir)

    else:
        with TemporaryDirectory() as cachedir:
            d = DNFuq(path, label=label, arch=arch, cachedir=cachedir)
            yield d
            d.cachedir = None
            d.sack = None


class DNFuq:
    """
    Utility class for creating queries against a dnf repository.
    Takes care of most of the dnf wiring lazily.

    :since: 2.1
    """

    def __init__(
            self,
            path: str,
            label: str = "koji",
            arch: str = None,
            cachedir: str = None):

        """
        :param path: path to the repository

        :param label: repository label, for use in storing the
          repository cache

        :param arch: override the architecture. By default the local
          system architecture is used.

        :param cachedir: the base directory for storing repository
          caches. If omitted the system temp directory will be used.
        """

        self.path: str = path
        self.label: str = label
        self.cachedir: str = cachedir
        self.arch: str = arch
        self.sack: SackType = None


    def query(self) -> QueryType:
        """
        produces a new query for the repository

        :raises DNFUnavailable: if the dnf module is not available
        """

        if self.sack is None:
            conf = dnf_config(self.cachedir, arch=self.arch)
            self.sack = dnf_sack(conf, self.path, self.label)
        return self.sack.query()


    def search(self,
               keys: List[str] = None,
               ownsfiles: List[str] = None,
               whatconflicts: List[str] = None,
               whatdepends: List[str] = None,
               whatobsoletes: List[str] = None,
               whatprovides: List[str] = None,
               whatrequires: List[str] = None,
               whatrecommends: List[str] = None,
               whatenhances: List[str] = None,
               whatsuggests: List[str] = None,
               whatsupplements: List[str] = None) -> QueryType:

        q = self.query()

        if keys:
            kq = q.filter(empty=True)
            for key in keys:
                subj = Subject(key, ignore_case=True)
                sq = subj.get_best_query(self.sack, with_provides=False,
                                         query=q)
                kq = kq.union(sq)
            q = kq

        if ownsfiles:
            q = q.filterm(file__glob=ownsfiles)
        if whatconflicts:
            q = q.filterm(conflicts__glob=whatconflicts)
        if whatdepends:
            # TODO: dnf with exactdeps enabled considers depends to
            # also include requires, recommends, enhances,
            # supplements, and suggests. We might want to support
            # that, too
            q = q.filterm(depends__glob=whatdepends)
        if whatobsoletes:
            q = q.filterm(obsoletes__glob=whatobsoletes)
        if whatprovides:
            q = q.filterm(provides__glob=whatprovides)
        if whatrequires:
            q = q.filterm(requires__glob=whatrequires)
        if whatrecommends:
            q = q.filterm(recommends__glob=whatrecommends)
        if whatenhances:
            q = q.filterm(enhances__glob=whatenhances)
        if whatsuggests:
            q = q.filterm(suggests__glob=whatsuggests)
        if whatsupplements:
            q = q.filterm(supplements__glob=whatsupplements)

        return q


def correlate_query_builds(
        session: ClientSession,
        found: List[PackageType]) -> List[Tuple[PackageType, BuildInfo]]:

    """
    Given a list of dnf query result Packages, correlate the
    packages back to koji builds

    :param session: an active koji client session

    :param found: the results of a dnf query, to be correlated back to
      koji build infos based on their source_name, version, and
      release

    :since: 2.1
    """

    # we cannot simply rely on source_name alone, because annoyingly
    # some subpackages will have a different version. Fortunately most
    # have a sourcerpm value which we can just trip the ".src.rpm" off
    # of.

    # nvrs = [f"{p.source_name}-{p.v}-{p.r}" for p in found]

    nvrs = [f"{p.sourcerpm[:-8]}" or
            f"{p.source_name}-{p.v}-{p.r}" for p in found]

    blds = bulk_load_builds(session, nvrs)
    return [(p, blds[nvr]) for nvr, p in zip(nvrs, found)]


_FMT_MATCH = compile_re(r'%(-?\d*?){(build\.|tag\.)?([:\w]+?)}')

_FMT_TAGS = (
    'arch', 'buildtime', 'conflicts', 'debug_name', 'description',
    'downloadsize', 'enhances', 'epoch', 'evr', 'from_repo', 'group',
    'installsize', 'installtime', 'license', 'name', 'obsoletes',
    'packager', 'provides', 'reason', 'recommends', 'release', 'repoid',
    'reponame', 'requires', 'size', 'source_debug_name', 'source_name',
    'sourcerpm', 'suggests', 'summary', 'supplements', 'url', 'vendor',
    'version', )


def _escape_brackets(txt: str) -> str:
    return txt.replace('{', '{{').replace('}', '}}')


def _fmt_repl(matchobj):
    fill, obj, key = matchobj.groups()
    key = key.lower()

    if not obj:
        if key not in _FMT_TAGS:
            return _escape_brackets(matchobj.group())
        else:
            obj = "rpm."

    if fill:
        fill = f":>{fill[1:]}" if fill[0] == '-' else f":<{fill}"
        return f"{{{obj}{key}{fill}}}"
    else:
        return f"{{{obj}{key}}}"


class PackageWrapper:

    def __init__(self, pkg: PackageType):
        self._pkg = pkg
        self._fields = None
        self._iters = None


    def __getattr__(self, attr):
        if self._iters is not None:
            fi = next(self._iters)
            result = next(fi)

        else:
            found = getattr(self._pkg, attr)

            if isinstance(found, list):
                if found:
                    found = sorted(map(ucd, found))
                    result = found[0]
                    found = found[1:]
                else:
                    found = result = "(none)"

            elif found is None:
                found = result = "(none)"

            else:
                found = result = ucd(found)
                result = ucd(found)

            if self._fields is not None:
                self._fields.append(found)

        return result


    def iter_format(self, formatter, build, tag):
        # first we populate the internal list of fields. Note that
        # this is a list and not a map, because there may be
        # duplicates in the formatter.

        self._fields = []
        res = formatter(rpm=self, build=build, tag=tag)
        yield res

        for f in self._fields:
            if isinstance(f, list):
                break
        else:
            # no lists, we're done.
            self._field = None
            return

        its = [iter(f) if isinstance(f, list) else repeat(f)
               for f in self._fields]
        self._iters = cycle(its)

        try:
            while True:
                yield formatter(rpm=self, build=build, tag=tag)
        except StopIteration:
            self._fields = None
            self._iters = None


DNFuqFormatter: TypeAlias = Callable[[PackageType, BuildInfo, TagInfo],
                                     Generator[str, None, None]]


def dnfuq_formatter(queryformat: str) -> DNFuqFormatter:
    # TODO: I'd love to support the rpm query format convention for
    # arrays here, but for now it's only an adaptation of what's in
    # dnf

    # ref:
    # https://rpm-software-management.github.io/rpm/manual/queryformat.html

    """
    Produces a formatter function based on a queryformat input
    string. This formatter can be invoked with three parameters -- a
    hawkey package, a build info dict, and a tag info dict. The result
    will be a string that interpolates fields from the three params.

    :param queryformat: The format string

    :since: 2.1
    """

    queryformat = queryformat.replace(r"\n", "\n").replace(r"\t", "\t")

    fmtl = []
    spos = 0
    for item in _FMT_MATCH.finditer(queryformat):
        fmtl.append(_escape_brackets(queryformat[spos:item.start()]))
        fmtl.append(_fmt_repl(item))
        spos = item.end()
    fmtl.append(_escape_brackets(queryformat[spos:]))

    fmts = "".join(fmtl)

    def formatter(pkg: PackageType, build: BuildInfo, tag: TagInfo):
        i = PackageWrapper(pkg)
        yield from i.iter_format(fmts.format,
                                 build=SimpleNamespace(**build),
                                 tag=SimpleNamespace(**tag))

    return formatter


#
# The end.
