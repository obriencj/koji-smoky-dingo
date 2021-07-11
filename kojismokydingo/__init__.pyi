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
    Any, Callable, Dict, Iterator, Iterable,
    Optional, Tuple, Union )


from .types import (
    ArchiveInfo, ArchiveSpec,
    BuildInfo, BuildSpec,
    HostInfo, HostSpec,
    RPMInfo, RPMSpec,
    TagInfo, TagSpec,
    TargetInfo, TargetSpec,
    TaskInfo, TaskSpec,
    UserInfo, UserSpec, )


class ManagedClientSession(ClientSession):
    def __enter__(self):
        ...

    def __exit__(self, exc_type: Any, _exc_val: Any, _exc_tb: Any):
        ...


class ProfileClientSession(ManagedClientSession):
    def __init__(self, profile: str = ...) -> None:
        ...


class AnonClientSession(ProfileClientSession):
    def __enter__(self):
        ...


class BadDingo(Exception):
    complaint: str = ...


class NoSuchBuild(BadDingo):
    complaint: str = ...


class NoSuchHost(BadDingo):
    complaint: str = ...


class NoSuchChannel(BadDingo):
    complaint: str = ...


class NoSuchContentGenerator(BadDingo):
    complaint: str = ...


class NoSuchTag(BadDingo):
    complaint: str = ...


class NoSuchTarget(BadDingo):
    complaint: str = ...


class NoSuchTask(BadDingo):
    complaint: str = ...


class NoSuchUser(BadDingo):
    complaint: str = ...


class NoSuchPermission(BadDingo):
    complaint: str = ...


class NoSuchArchive(BadDingo):
    complaint: str = ...


class NoSuchRPM(BadDingo):
    complaint: str = ...


class NotPermitted(BadDingo):
    complaint: str = ...


class FeatureUnavailable(BadDingo):
    complaint: str = ...


def iter_bulk_load(
        session: ClientSession,
        loadfn: Callable[[Any], Any],
        keys: Iterable[Any],
        err: bool = ...,
        size: int = ...) -> Iterator[Tuple[Any, Any]]:
    ...


def bulk_load(
        session: ClientSession,
        loadfn: Callable[[Any], Any],
        keys: Iterable[Any],
        err: bool = ...,
        size: int = ...,
        results: Optional[dict] = ...) -> Dict[Any, Any]:
    ...


def bulk_load_builds(
        session: ClientSession,
        nvrs: Iterable[Union[str, int]],
        err: bool = ...,
        size: int = ...,
        results: Optional[dict] = ...) -> Dict[Union[int, str],
                                               Optional[BuildInfo]]:
    ...


def bulk_load_tasks(
        session: ClientSession,
        task_ids: Iterable[int],
        request: bool = ...,
        err: bool = ...,
        size: int = ...,
        results: Optional[dict] = ...) -> Dict[int, Optional[TaskInfo]]:
    ...


def bulk_load_tags(
        session: ClientSession,
        tags: Iterable[Union[str, int]],
        err: bool = ...,
        size: int = ...,
        results: Optional[dict] = ...) -> Dict[Union[int, str],
                                               Optional[TagInfo]]:
    ...


def bulk_load_rpm_sigs(session: Any, rpm_ids: Any, size: int = ..., results: Optional[Any] = ...): ...
def bulk_load_buildroot_archives(session: Any, buildroot_ids: Any, btype: Optional[Any] = ..., size: int = ..., results: Optional[Any] = ...): ...
def bulk_load_buildroot_rpms(session: Any, buildroot_ids: Any, size: int = ..., results: Optional[Any] = ...): ...
def bulk_load_build_archives(session: Any, build_ids: Any, btype: Optional[Any] = ..., size: int = ..., results: Optional[Any] = ...): ...
def bulk_load_build_rpms(session: Any, build_ids: Any, size: int = ..., results: Optional[Any] = ...): ...
def bulk_load_buildroots(session: Any, broot_ids: Any, size: int = ..., results: Optional[Any] = ...): ...
def bulk_load_users(session: Any, users: Any, err: bool = ..., size: int = ..., results: Optional[Any] = ...): ...


def as_buildinfo(
        session: ClientSession,
        build: BuildSpec) -> BuildInfo:
    ...


def as_taginfo(
        session: ClientSession,
        tag: TagSpec) -> TagInfo:
    ...


def as_taskinfo(
        session: ClientSession,
        task: TaskSpec) -> TaskInfo:
    ...


def as_targetinfo(
        session: ClientSession,
        target: TargetSpec) -> TargetInfo:
    ...


def as_hostinfo(
        session: ClientSession,
        host: HostSpec) -> HostInfo:
    ...


def as_archiveinfo(
        session: ClientSession,
        archive: ArchiveSpec) -> ArchiveInfo:
    ...


def as_rpminfo(
        session: ClientSession,
        rpm: RPMSpec) -> RPMInfo:
    ...


def as_userinfo(
        session: ClientSession,
        user: UserSpec) -> UserInfo:
    ...


def hub_version(
        session: ClientSession) -> Tuple[int]:
    ...


def version_check(
        session: ClientSession,
        minimum: Tuple[int] = ...) -> bool:
    ...


def version_require(
        session: Any,
        minimum: Any = ...,
        message: Optional[Any] = ...) -> bool:
    ...


#
# The end.
