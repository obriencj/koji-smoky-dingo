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
from typing import Dict, Iterable, List, Optional, Set, Union

from .types import (
    DecoratedTagExtras,
    TagInfo, TagInfos, TagInheritance, TagInheritanceEntry,
    TagSpec, TargetInfos, )


def tag_dedup(
        tag_infos: TagInfos) -> TagInfos:
    ...


def ensure_tag(
        session: ClientSession,
        name: str) -> TagInfo:
    ...


def resolve_tag(
        session: ClientSession,
        name: str,
        target: bool = ...) -> TagInfo:
    ...


def gather_affected_targets(
        session: ClientSession,
        tagnames: Iterable[TagSpec]) -> TargetInfos:
    ...


def renum_inheritance(
        inheritance: TagInheritance,
        begin: int = ...,
        step: int = ...) -> TagInheritance:
    ...


def find_inheritance_parent(
        inheritance: TagInheritance,
        parent_id: int) -> Optional[TagInheritanceEntry]:
    ...


def convert_tag_extras(
        taginfo: TagInfo,
        into: Optional[dict] = ...,
        prefix: Optional[str] = ...) -> DecoratedTagExtras:
    ...


def collect_tag_extras(
        session: ClientSession,
        taginfo: TagSpec,
        prefix: Optional[str] = ...) -> DecoratedTagExtras:
    ...


def gather_tag_ids(
        session: ClientSession,
        shallow: Optional[Iterable[Union[int, str]]] = ...,
        deep: Optional[Iterable[Union[int, str]]] = ...,
        results: Optional[set] = ...) -> Set[int]:
    ...


#
# The end.
