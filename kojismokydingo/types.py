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
Koji Smoky Dingo - Type Definitions

Python typing compatible definitions for the Koji dict types and
enumerations

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from datetime import datetime
from enum import IntEnum
from koji import (
    AUTHTYPES, BR_STATES, BR_TYPES, BUILD_STATES, CHECKSUM_TYPES,
    REPO_STATES, TASK_STATES, USERTYPES, USER_STATUS,
    ClientSession, PathInfo, )
from koji_types import (
    ArchiveInfo, ATypeInfo, AuthType, BuildInfo,
    BuildrootInfo, BuildrootState, BuildrootType, BuildState,
    BTypeInfo, ChannelInfo, ChecksumType, CGInfo,
    GOptions, HistoryEntry, HostInfo, ListTasksOptions, PackageInfo,
    PermInfo, QueryOptions, RepoInfo, RepoState, RPMInfo,
    RPMSignature, SearchResult, TagBuildInfo, TagInfo,
    TagInheritance, TagInheritanceEntry, TagGroupInfo, TagGroupPackage,
    TagGroupReq, TagPackageInfo, TargetInfo, TaskInfo,
    TaskState, UserGroup, UserInfo, UserStatus, UserType, )
from koji_types.cli import CLIHandler, CLIProtocol
from optparse import Values
from typing import (
    Any, Callable, Dict, Generic, Iterable, List, Optional,
    Tuple, TypeVar, Union, )


try:
    from typing import TypedDict  # type: ignore
except ImportError:
    # Python < 3.10 doesn't have typing.TypedDict
    from typing_extensions import TypedDict


__all__ = (
    "ArchiveInfo",
    "ArchiveInfos",
    "ArchiveSpec",
    "ArchiveTypeInfo",
    "AuthType",
    "BuildInfo",
    "BuildInfos",
    "BuildrootInfo",
    "BuildrootState",
    "BuildrootType",
    "BuildSpec",
    "BuildState",
    "BTypeInfo",
    "ChannelInfo",
    "ChannelSpec",
    "ChecksumType",
    "CGInfo",
    "CLIHandler",
    "CLIProtocol",
    "DecoratedBuildInfo",
    "DecoratedHostInfo",
    "DecoratedHostInfos",
    "DecoratedTagExtra",
    "DecoratedTagExtras",
    "DecoratedPermInfo",
    "DecoratedUserInfo",
    "GOptions",
    "HistoryEntry",
    "HostInfo",
    "HubVersionSpec",
    "KeySpec",
    "ListTasksOptions",
    "NamedCGInfo",
    "PackageInfo",
    "PackageSpec",
    "PathSpec",
    "PermInfo",
    "PermSpec",
    "PermUser",
    "QueryOptions",
    "RepoInfo",
    "RepoState",
    "RPMInfo",
    "RPMInfos",
    "RPMSignature",
    "RPMSpec",
    "SearchResult",
    "TagBuildInfo",
    "TagInfo",
    "TagInfos",
    "TagInheritance",
    "TagInheritanceEntry",
    "TagGroupInfo",
    "TagGroupPackage",
    "TagGroupReq",
    "TagPackageInfo",
    "TagSpec",
    "TargetInfo",
    "TargetInfos",
    "TargetSpec",
    "TaskInfo",
    "TaskSpec",
    "TaskState",
    "UserGroup",
    "UserInfo",
    "UserSpec",
    "UserStatus",
    "UserStatistics",
    "UserType",
)


HubVersionSpec = Union[str, Tuple[int, ...]]
"""
a koji version requirement, specified as either a string or tuple
of ints. See `kojismokydingo.version_check` and
`kojismokydingo.version_require`

  * ``"1.25"``
  * ``(1, 25)``
"""


ArchiveTypeInfo = ATypeInfo


ArchiveInfos = Iterable[ArchiveInfo]


BuildInfos = Iterable[BuildInfo]


RPMInfos = Iterable[RPMInfo]


TagInfos = Iterable[TagInfo]


TargetInfos = Iterable[TargetInfo]


class DecoratedArchiveInfo(ArchiveInfo):
    filepath: str


DecoratedArchiveInfos = Iterable[DecoratedArchiveInfo]


ArchiveSpec = Union[int, str, ArchiveInfo]
"""
An archive ID, filename, or info dict
"""


class DecoratedBuildInfo(BuildInfo):

    archive_btype_names: List[str]
    archive_btype_ids: List[int]

    archive_cg_names: List[str]
    archive_cg_ids: List[int]


DecoratedBuildInfos = Iterable[DecoratedBuildInfo]
"""
An Iterable of DecoratedBuildInfo dicts
"""


BuildSpec = Union[int, str, BuildInfo]
"""
An indicator for a build in cases where the build may be
communicated as its ID, its NVR, or as an already-loaded BuildInfo
"""


PathSpec = Union[str, PathInfo]
"""

"""


RPMSpec = Union[int, str, RPMInfo]
"""
Ways to indicate an RPM to `as_rpminfo`
"""


class DecoratedRPMInfo(RPMInfo):
    """
    Returned by `kojismokydingo.archives.gather_signed_rpms` Simply an
    `RPMInfo` dict with a single additional field representing which
    preferred signature (if any) was available.
    """

    btype: str
    btype_id: int

    filepath: str

    sigkey: str

    type_id: int
    type_name: str


DecoratedRPMInfos = Iterable[DecoratedRPMInfo]


HostSpec = Union[int, str, HostInfo]
"""
Acceptable ways to specify a host
"""


class DecoratedHostInfo(HostInfo):
    last_update: datetime
    """ The last time that a host checked in with an update """


DecoratedHostInfos = Iterable[DecoratedHostInfo]


UserSpec = Union[int, str, UserInfo]
"""
Acceptable ways to specify a user, either by a UserInfo dict, a
username str, or a user's int ID
"""


class NamedCGInfo(CGInfo):
    """
    A CGInfo with its name merged into it. Obtained via
    `kojismokydingo.users.collect_cgs`
    """

    name: str
    """ friendly name for this content generator """


class PermUser(TypedDict):
    user_name: str
    permission_name: str
    create_ts: float
    create_date: datetime


class DecoratedPermInfo(PermInfo):
    """
    A `PermInfo` decorated with the list of users that have been
    granted the permission. Obtained via
    `kojismokydingo.users.collect_perminfo`
    """

    users: List[PermUser]


PermSpec = Union[int, str]
"""
a permission's ID or name
"""


class UserStatistics(TypedDict):

    build_count: int
    """ count of builds owned by this user """

    package_count: int
    """ count of packages owned by this user """

    task_count: int
    """ count of tasks submitted by this user """

    last_build: Optional["BuildInfo"]
    """ the most recent build by this user """

    last_task: Optional["TaskInfo"]
    """ the most recent task by this user """


class DecoratedUserInfo(UserInfo):
    """
    A `UserInfo` decorated with additional fields that merge more data
    together from other calls. Obtained via
    `kojismokydingo.users.collect_userinfo`
    """

    permissions: List[str]
    """ names of granted permissions """

    content_generators: List[NamedCGInfo]
    """ names of granted content generators """

    ksd_members: List[UserInfo]
    """ membership if user is a group """

    ksd_groups: List[UserGroup]
    """ groups that user is a member of """

    statistics: Optional[UserStatistics]
    """ user's interaction statistics """


RepoSpec = Union[int, RepoInfo, str, 'TagInfo']
"""
`kojismokydingo.as_repoinfo`
"""


TargetSpec = Union[int, str, TargetInfo]
"""
An indicator for a target in cases where it may be communicated by
its ID, its name, or an already-loaded TargetInfo
"""


TagSpec = Union[int, str, TagInfo]
"""
An indicator for a tag in cases where it may be communicated by
its ID, its name, or as an already-loaded TagInfo
"""


class DecoratedTagExtra(TypedDict):
    blocked: bool
    name: str
    tag_name: str
    tag_id: int
    value: str


DecoratedTagExtras = Dict[str, DecoratedTagExtra]


PackageSpec = Union[int, str, PackageInfo]
"""
`kojismokydingo.as_packageinfo`
"""


TaskSpec = Union[int, TaskInfo]
"""
task ID or TaskInfo dict
"""


ChannelSpec = Union[int, str, ChannelInfo]


KeySpec = Union[Callable[[Any], Any], Any]
"""
a key specifier, used as either an index/item lookup on objects, or a
unary callable which returns the desired field.

Typically non callable keyspec values are converted into an itemgetter
using that value.
"""


#
# The end.
