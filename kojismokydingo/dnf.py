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
from koji import ClientSession
from os.path import abspath
from tempfile import TemporaryDirectory
from typing import Any, Generator, List, Tuple

from . import BadDingo, bulk_load_builds
from .types import BuildInfo


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
    from dnf.package import Package
    from dnf.query import Query
    from dnf.sack import Sack, _build_sack

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
)


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
def dnf_config(cachedir: str = None) -> MainConfType:
    """
    produces a dnf main configuration appropriate for use outside
    of managing a local system

    :param cachedir: the base directory to create per-repository
      caches in. If omitted the system temp directory will be used

    :raises DNFUnavailable: if the dnf module is not available

    :raises ValueError: if cachedir is not suppled

    :since: 2.1
    """

    if not cachedir:
        raise ValueError("cannot execute query without a cachedir")

    mc = MainConf()
    mc.cachedir = cachedir

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

    base._sack = _build_sack(base)
    base._add_repo_to_sack(base.repos[label])

    return base.sack


@contextmanager
@requires_dnf
def dnfuq(path: str,
          label: str = "koji",
          cachedir: str = None) -> Generator["DNFuq", None, None]:

    """
    context manager providing a DNFuq instance configured with
    either a re-usable or temporary cache directory.

    :param path: path to the repository

    :param label: repository label, for use in storing the repository
      cache

    :param cachedir: the base directory for storing repository
      caches. If omitted the system temp directory will be used, and
      the cache will be deleted afterwards.

    :raises DNFUnavailable: if the dnf module is not available

    :since: 2.1
    """

    if cachedir:
        yield DNFuq(path, label, cachedir)

    else:
        with TemporaryDirectory() as cachedir:
            d = DNFuq(path, label, cachedir)
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
            cachedir: str = None):

        """
        :param path: path to the repository

        :param label: repository label, for use in storing the
          repository cache

        :param cachedir: the base directory for storing repository
          caches. If omitted the system temp directory will be used.
        """

        self.path: str = path
        self.label: str = label
        self.cachedir: str = cachedir
        self.sack: SackType = None


    def query(self) -> QueryType:
        """
        produces a new query for the repository

        :raises DNFUnavailable: if the dnf module is not available
        """

        if self.sack is None:
            conf = dnf_config(self.cachedir)
            self.sack = dnf_sack(conf, self.path, self.label)
        return self.sack.query()


    def whatprovides(self, ask: str) -> List[PackageType]:
        """
        runs a provides query on the repository

        :param ask: the provides glob term to search for

        :raises DNFUnavailable: if the dnf module is not available
        """

        q = self.query().filterm(provides__glob=ask)
        return q.run()


    def whatrequires(self, ask: str) -> List[PackageType]:
        """
        runs a requires query on the repository

        :param ask: the requires glob term to search for

        :raises DNFUnavailable: if the dnf module is not available
        """

        q = self.query().filterm(requires__glob=ask)
        return q.run()


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

    nvrs = [f"{p.source_name}-{p.v}-{p.r}" for p in found]
    blds = bulk_load_builds(session, nvrs)
    return [(p, blds[nvr]) for nvr, p in zip(nvrs, found)]


#
# The end.
