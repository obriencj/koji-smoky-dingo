from .types import ArchiveInfos
from koji import ClientSession, PathInfo
from typing import Any, Iterable, Optional, Union

def as_pathinfo(path: Union[str, PathInfo]) -> PathInfo: ...
def filter_archives(session: ClientSession, archives: ArchiveInfos, archive_types: Iterable[str]=..., arches: Iterable[str]=...) -> ArchiveInfos: ...
def gather_signed_rpms(session: Any, archives: Any, sigkeys: Any): ...
def gather_build_rpms(session: Any, binfo: Any, rpmkeys: Any = ..., path: Optional[Any] = ...): ...
def gather_build_maven_archives(session: Any, binfo: Any, path: Optional[Any] = ...): ...
def gather_build_win_archives(session: Any, binfo: Any, path: Optional[Any] = ...): ...
def gather_build_image_archives(session: Any, binfo: Any, path: Optional[Any] = ...): ...
def gather_build_archives(session: Any, binfo: Any, btype: Optional[Any] = ..., rpmkeys: Any = ..., path: Optional[Any] = ...): ...
def gather_latest_rpms(session: Any, tagname: Any, rpmkeys: Any = ..., iherit: bool = ..., path: Optional[Any] = ...): ...
def gather_latest_maven_archives(session: Any, tagname: Any, inherit: bool = ..., path: Optional[Any] = ...): ...
def gather_latest_win_archives(session: Any, tagname: Any, inherit: bool = ..., path: Optional[Any] = ...): ...
def gather_latest_image_archives(session: Any, tagname: Any, inherit: bool = ..., path: Optional[Any] = ...): ...
def gather_latest_archives(session: Any, tagname: Any, btype: Optional[Any] = ..., rpmkeys: Any = ..., inherit: bool = ..., path: Optional[Any] = ...): ...
