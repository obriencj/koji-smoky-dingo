from enum import IntEnum
from typing import Any, Iterable, List, Optional, Union
from typing_extensions import TypedDict

class ArchiveChecksum(IntEnum):
    MD5: int = ...
    SHA1: int = ...
    SHA256: int = ...

class ArchiveInfo(TypedDict):
    btype: str
    btype_id: int
    build_id: int
    buildroot_id: int
    checksum: str
    checksum_type: int
    extra: Optional[dict]
    filename: str
    id: int
    metadata_only: bool
    size: int
    type_description: str
    type_extensions: str
    type_id: int
    type_name: str
ArchiveInfos = Iterable[ArchiveInfo]

class BuildState(IntEnum):
    BUILDING: Any = ...
    COMPLETE: Any = ...
    DELETED: Any = ...
    FAILED: Any = ...
    CANCELED: Any = ...

class BuildInfo(TypedDict):
    build_id: int
    cg_id: Optional[int]
    cg_name: Optional[str]
    completion_time: str
    completion_ts: Union[int, float]
    creation_event_id: int
    creation_time: str
    creation_ts: Union[int, float]
    epoch: Optional[str]
    extra: Optional[dict]
    id: int
    name: str
    nvr: str
    owner_id: int
    owner_name: str
    package_id: int
    package_name: str
    release: str
    source: Optional[str]
    start_time: Optional[str]
    start_ts: Optional[Union[int, float]]
    state: int
    task_id: Optional[int]
    version: str
    volume_id: int
    volume_name: str
BuildInfos = Iterable[BuildInfo]

class MavenArchiveInfo(ArchiveInfo):
    artifact_id: str
    group_id: str
    version: str

class RPMInfo(TypedDict):
    arch: str
    build_id: int
    buildroot_id: int
    buildtime: int
    epoch: Optional[str]
    external_repo_id: int
    external_repo_name: str
    extra: Optional[dict]
    id: int
    metadata_only: bool
    name: str
    nvr: str
    payloadhash: str
    release: str
    size: int
    version: str

class WindowsArchiveInfo(ArchiveInfo):
    platforms: List[str]
