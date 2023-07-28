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
Koji Smoky Dingo - DNF ease-of-use wrapper

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from contextlib import contextmanager
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


BaseType: TypeAlias
MainConfType: TypeAlias
PackageType: TypeAlias
QueryType: TypeAlias
SackType: TypeAlias


try:
    from dnf.base import Base
    from dnf.conf.config import MainConf
    from dnf.sack import Sack, _build_sack
    from hawkey import Package, Query

except ImportError:
    ENABLED = False

    BaseType = Any
    MainConfType = Any
    PackageType = Any
    QueryType = Any
    SackType = Any

else:
    ENABLED = True

    BaseType = Base
    MainConfType = MainConf
    PackageType = Package
    QueryType = Query
    SackType = Sack


class DNFuqError(BadDingo):
    complaint = "dnf error"


def __requirednf():
    if not ENABLED:
        raise DNFuqError("dnf package not found")


def dnf_config(cachedir: str) -> MainConfType:

    __requirednf()

    if not cachedir:
        raise DNFuqError("cannot execute query without a cachedir")

    mc = MainConf()
    mc.cachedir = cachedir

    return mc


def dnf_sack(config: MainConfType,
             path: str,
             label: str = "koji") -> SackType:

    __requirednf()

    if "://" not in path:
        path = "file://" + abspath(path)

    base = Base(config)
    base.repos.add_new_repo(label, config, baseurl=[path])

    base._sack = _build_sack(base)
    base._add_repo_to_sack(base.repos[label])

    return base.sack


def correlate_query_builds(
        session: ClientSession,
        found: List[PackageType]) -> List[Tuple[PackageType, BuildInfo]]:

    """
    Given a list of dnf query result Packages, correlate the packages
    back to koji builds
    """

    nvrs = [f"{p.source_name}-{p.v}-{p.r}" for p in found]
    blds = bulk_load_builds(session, nvrs)
    return [(p, blds[nvr]) for nvr, p in zip(nvrs, found)]


@contextmanager
def dnfuq(path: str,
          label: str = "koji",
          cachedir: str = None) -> Generator["DNFuq", None, None]:

    """
    context manager providing a DNFuq instance configured with a
    temporary cache directory which will be cleaned up on exit
    """

    __requirednf()

    with TemporaryDirectory(dir=cachedir) as tmpdir:
        d = DNFuq(path, label, tmpdir)
        yield d
        d.cachedir = None
        d.sack = None


class DNFuq:

    def __init__(
            self,
            path: str,
            label: str = "koji",
            cachedir: str = None):

        self.path: str = path
        self.label: str = label
        self.cachedir: str = cachedir
        self.sack: SackType = None


    def query(self) -> QueryType:
        if self.sack is None:
            conf = dnf_config(self.cachedir)
            self.sack = dnf_sack(conf, self.path, self.label)
        return self.sack.query()


    def whatprovides(self, ask: str) -> List[PackageType]:
        q = self.query().filterm(provides__glob=ask)
        return q.run()


    def whatrequires(self, ask: str) -> List[PackageType]:
        q = self.query().filterm(requires__glob=ask)
        return q.run()


#
# The end.
