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


from typing import Any, Iterable, Optional, Union
from koji import ClientSession, PathInfo

from .types import (
    ArchiveInfos, BuildInfo, DecoratedArchiveInfos, DecoratedRPMInfos,
    ImageArchiveInfos, MavenArchiveInfos, PathSpec, SignedRPMInfo,
    WindowsArchiveInfos, )


def as_pathinfo(
        path: PathSpec) -> PathInfo:
    ...


def filter_archives(
        session: ClientSession,
        archives: ArchiveInfos,
        archive_types: Iterable[str] = ...,
        arches: Iterable[str] = ...) -> ArchiveInfos:
    ...


def gather_signed_rpms(
        session: ClientSession,
        archives: ArchiveInfos,
        sigkeys: Iterable[str]) -> DecoratedRPMInfos:
    ...


def gather_build_rpms(
        session: ClientSession,
        binfo: BuildInfo,
        rpmkeys: Optional[Iterable[str]] = ...,
        path: Optional[Union[str, PathInfo]] = ...) -> DecoratedRPMInfos:
    ...


def gather_build_maven_archives(
        session: ClientSession,
        binfo: BuildInfo,
        path: Optional[PathSpec] = ...) -> MavenArchiveInfos:
    ...


def gather_build_win_archives(
        session: ClientSession,
        binfo: BuildInfo,
        path: Optional[PathSpec] = ...) -> WindowsArchiveInfos:
    ...


def gather_build_image_archives(
        session: ClientSession,
        binfo: BuildInfo,
        path: Optional[PathSpec] = ...) -> ImageArchiveInfos:
    ...


def gather_build_archives(
        session: ClientSession,
        binfo: BuildInfo,
        btype: Optional[str] = ...,
        rpmkeys: Optional[Iterable[str]] = ...,
        path: Optional[PathSpec] = ...) -> DecoratedArchiveInfos:
    ...


def gather_latest_rpms(
        session: ClientSession,
        tagname: str,
        rpmkeys: Optional[Iterable[str]] = ...,
        inherit: bool = ...,
        path: Optional[PathSpec] = ...) -> DecoratedArchiveInfos:
    ...


def gather_latest_maven_archives(
        session: ClientSession,
        tagname: str,
        inherit: bool = ...,
        path: Optional[PathSpec] = ...) -> MavenArchiveInfos:
    ...


def gather_latest_win_archives(
        session: ClientSession,
        tagname: str,
        inherit: bool = ...,
        path: Optional[PathSpec] = ...) -> WindowsArchiveInfos:
    ...


def gather_latest_image_archives(
        session: ClientSession,
        tagname: str,
        inherit: bool = ...,
        path: Optional[PathSpec] = ...) -> ImageArchiveInfos:
    ...


def gather_latest_archives(
        session: ClientSession,
        tagname: str,
        btype: Optional[str] = ...,
        rpmkeys: Optional[Iterable[str]] = ...,
        inherit: bool = ...,
        path: Optional[PathSpec] = ...) -> ArchiveInfos:
    ...


#
# The end.
