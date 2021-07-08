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


from koji import ClientSession
from typing import (
    Any, Callable, Dict, Generator, Iterable, Iterator,
    List, Optional, Tuple, Union, )

from .types import (
    BuildInfo, BuildInfos, BuildState,
    DecoratedBuildInfos, MavenBuildInfo, TagSpec, )


class NEVRCompare:
    n: str = ...
    evr: Tuple[str, str, str] = ...

    def __init__(
            self,
            name: str,
            epoch: Optional[str],
            version: Optional[str],
            release: Optional[str]) -> None:
        ...


class BuildNEVRCompare(NEVRCompare):
    build: BuildInfo = ...

    def __init__(
            self,
            binfo: BuildInfo) -> None:
        ...


gavgetter: Callable[[Tuple[str]], BuildInfo]


def build_nvr_sort(
        build_infos: BuildInfos,
        dedup: bool=...,
        reverse: bool=...) -> BuildInfos:
    ...


def build_id_sort(
        build_infos: BuildInfos,
        dedup: bool=...,
        reverse: bool=...) -> BuildInfos:
    ...


def build_dedup(
        build_infos: BuildInfos) -> BuildInfos:
    ...


def iter_bulk_move_builds(
        session: ClientSession,
        srctag: TagSpec,
        dsttag: TagSpec,
        build_infos: BuildInfos,
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> Iterator[List[Tuple[BuildInfo, Any]]]:
    ...


def bulk_move_builds(
        session: ClientSession,
        srctag: TagSpec,
        dsttag: TagSpec,
        build_infos: BuildInfos,
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> List[Tuple[BuildInfo, Any]]:
    ...


def bulk_move_nvrs(
        session: ClientSession,
        srctag: TagSpec,
        dsttag: TagSpec,
        nvrs: Iterable[Union[int, str]],
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> List[Tuple[BuildInfo, Any]]:
    ...


def iter_bulk_tag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> Iterator[List[Tuple[BuildInfo, Any]]]:
    ...


def bulk_tag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> List[Tuple[BuildInfo, Any]]:
    ...


def bulk_tag_nvrs(
        session: ClientSession,
        tag: TagSpec,
        nvrs: Iterable[Union[int, str]],
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> List[Tuple[BuildInfo, Any]]:
    ...


def iter_bulk_untag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> Iterator[List[Tuple[BuildInfo, Any]]]:
    ...


def bulk_untag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> List[Tuple[BuildInfo, Any]]:
    ...


def bulk_untag_nvrs(
        session: ClientSession,
        tag: TagSpec,
        nvrs: Iterable[Union[int, str]],
        force: bool = ...,
        notify: bool = ...,
        size: int = ...,
        strict: bool = ...) -> List[Tuple[BuildInfo, Any]]:
    ...


GAV = Tuple[str, str, str]


def iter_latest_maven_builds(
        session: ClientSession,
        tag: TagSpec,
        pkg_names: Optional[Iterable[str]] = ...,
        inherit: bool = ...) -> Iterator[Tuple[GAV, MavenBuildInfo]]:
    ...


def latest_maven_builds(
        session: ClientSession,
        tag: TagSpec,
        pkg_names: Optional[Iterable[str]] = ...,
        inherit: bool = ...) -> Dict[GAV, MavenBuildInfo]:
    ...


def decorate_builds_maven(
        session: ClientSession,
        build_infos: BuildInfos) -> DecoratedBuildInfos:
    ...


def decorate_builds_btypes(
        session: ClientSession,
        build_infos: BuildInfos,
        with_fields: bool = ...) -> DecoratedBuildInfos:
    ...


def decorate_builds_cg_list(
        session: ClientSession,
        build_infos: BuildInfos) -> DecoratedBuildInfos:
    ...


def filter_builds_by_tags(
        session: ClientSession,
        build_infos: BuildInfos,
        limit_tag_ids: Iterable[int] = ...,
        lookaside_tag_ids: Iterable[int] = ...) -> BuildInfos:
    ...


def filter_builds_by_state(
        build_infos: BuildInfos,
        state: BuildState = ...) -> BuildInfos:
    ...


def filter_imported_builds(build_infos: Any, by_cg: Any = ..., negate: bool = ...) -> None: ...
def gather_buildroots(session: Any, build_ids: Any): ...
def gather_rpm_sigkeys(session: Any, build_ids: Any): ...
def gather_wrapped_builds(session: Any, task_ids: Any, results: Optional[Any] = ...): ...
def gather_component_build_ids(session: Any, build_ids: Any, btypes: Optional[Any] = ...): ...


class BuildFilter:

    def __init__(
            self,
            session: ClientSession,
            limit_tag_ids: Optional[Any] = ...,
            lookaside_tag_ids: Optional[Any] = ...,
            imported: Optional[bool] = ...,
            cg_list: Optional[Any] = ...,
            btypes: Optional[Any] = ...,
            state: Optional[BuildState] = ...) -> None:
        ...

    def filter_by_tags(self, build_infos: BuildInfos) -> BuildInfos: ...
    def filter_by_btype(self, build_infos: BuildInfos) -> BuildInfos: ...
    def filter_imported(self, build_infos: BuildInfos) -> BuildInfos: ...
    def filter_by_state(self, build_infos: BuildInfos) -> BuildInfos: ...

    def __call__(self, build_infos: BuildInfos) -> BuildInfos:
        ...


#
# The end.
