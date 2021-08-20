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

Python typing compatible definitions for the Koji dict types


:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from datetime import datetime
from enum import IntEnum
from koji import (
    BUILD_STATES, CHECKSUM_TYPES, USERTYPES, USER_STATUS,
    PathInfo, )
from typing import (
    Any, Callable, Dict, Iterable, List, Tuple, Union, )


try:
    from typing import TypedDict

except ImportError:
    # Python < 3.8 doesn't have TypedDict yet, need to pull it in from
    # the typing_extensions backport instead.
    from typing_extensions import TypedDict


IterList = Union[Iterable, List]


__all__ = (
    "ArchiveInfo",
    "ArchiveInfos",
    "ArchiveSpec",
    "BuildInfo",
    "BuildInfos",
    "BuildSpec",
    "BuildState",
    "ChecksumType",
    "DecoratedHostInfo",
    "DecoratedHostInfos",
    "DecoratedTagExtra",
    "DecoratedTagExtras",
    "HostInfo",
    "HubVersionSpec",
    "KeySpec",
    "MavenArchiveInfo",
    "PathSpec",
    "PermInfo",
    "PermSpec",
    "RPMInfo",
    "RPMInfos",
    "RPMSignature",
    "RPMSpec",
    "TagInfo",
    "TagInfos",
    "TagInheritance",
    "TagInheritanceEntry",
    "TagSpec",
    "TargetInfo",
    "TargetInfos",
    "TargetSpec",
    "TaskInfo",
    "TaskSpec",
    "UserInfo",
    "UserSpec",
)


class ChecksumType(IntEnum):
    """
    Supported checksum types
    """

    MD5 = CHECKSUM_TYPES['md5']
    SHA1 = CHECKSUM_TYPES['sha1']
    SHA256 = CHECKSUM_TYPES['sha256']


class ArchiveInfo(TypedDict):
    """
    Data representing a koji archive. These are typically obtained via
    the ``getArchive`` or ``listArchives`` XMLRPC calls, or from the
    `kojismokydingo.as_archiveinfo` function
    """

    btype: str
    """ Name of this archive's koji BType. eg. 'maven' or 'image' """

    btype_id: int
    """ ID of this archive's koji BType """

    build_id: int
    """ ID of koji build owning this archive """

    buildroot_id: int
    """ ID of the koji buildroot used to produce this archive """

    checksum: str
    """ hex representation of the checksum for this archive """

    checksum_type: ChecksumType
    """ type of cryptographic checksum used in the `checksum` field """

    extra: dict
    """ additional metadata provided by content generators """

    filename: str
    """ base filename for this archive """

    id: int
    """ internal ID """

    metadata_only: bool

    size: int
    """ filesize in bytes """

    type_description: str
    """ this archive's type description """

    type_extensions: str
    """ space-delimited extensions shared by this archive's type """

    type_id: int
    """ ID of the archive's type """

    type_name: str
    """ name of the archive's type. eg. 'zip' or 'pom' """


ArchiveInfos = Iterable[ArchiveInfo]
""" An Iterable of ArchiveInfo dicts """


ArchiveSpec = Union[int, str, ArchiveInfo]
"""
An archive ID, filename, or info dict
"""


class BuildState(IntEnum):
    """
    Values for a BuildInfo's state.

    See `koji.BUILD_STATES`
    """

    BUILDING = BUILD_STATES["BUILDING"]
    """
    The build is still in-progress
    """

    COMPLETE = BUILD_STATES["COMPLETE"]
    """
    The build has been completed successfully
    """

    DELETED = BUILD_STATES["DELETED"]
    """
    The build has been deleted
    """

    FAILED = BUILD_STATES["FAILED"]
    """
    The build did not complete successfully due to an error
    """

    CANCELED = BUILD_STATES["CANCELED"]
    """
    The build did not complete successfully due to cancelation
    """


class BuildInfo(TypedDict):
    """
    Data representing a koji build. These are typically obtained via
    the ``getBuild`` XMLRPC call, or from the
    `kojismokydingo.as_buildinfo` function
    """

    build_id: int
    """ The internal ID for the build record """

    cg_id: int
    """ The ID of the content generator which has reserved or produced
    this build """

    cg_name: str
    """ The name of the content generator which has reserved or produced
    this build """

    completion_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this build
    was completed """

    completion_ts: Union[int, float]
    """ UTC timestamp indicating when this build was completed """

    creation_event_id: int
    """ koji event ID at the creation of this build record """

    creation_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this build
    record was created """

    creation_ts: Union[int, float]
    """ UTC timestamp indicating when this build record was created """

    epoch: str
    """ epoch of this build, or None if unspecified. This field is
    typically only used for RPM builds which have specified an epoch
    in their spec. """

    extra: dict
    """ flexible additional information for this build, used by content
    generators """

    id: int
    """ Same as build_id """

    name: str
    """ The name component of the NVR of this build. Should match the
    package_name field. """

    nvr: str
    """ The unique NVR of the build, comprised of the name, version, and
    release separated by hyphens """

    owner_id: int
    """ ID of the koji user that owns this build """

    owner_name: str
    """ name of the koji user that owns this build """

    package_id: int
    """ The corresponding package ID for this build. """

    package_name: str
    """ The corresponding package name for this build. Should match the
    name field. """

    release: str
    source: str
    start_time: str
    start_ts: Union[int, float]

    state: int
    """ state of the build, see `BuildState` """

    task_id: int

    version: str
    """ version portion of the NVR for the build """

    volume_id: int
    """ ID of the storage volume that the archives for this build will be
    stored on """

    volume_name: str
    """ name of the storage that the archives for this build will be
    stored on """


class MavenBuildInfo(BuildInfo):
    maven_group_id: str
    maven_artifact_id: str
    maven_version: str


class DecoratedBuildInfo(BuildInfo):
    archive_btype_names: List[str]
    archive_btype_ids: List[int]

    archive_cg_names: List[str]
    archive_cg_ids: List[int]

    maven_group_id: str
    maven_artifact_id: str
    maven_version: str

    platform: str


BuildInfos = Iterable[BuildInfo]
"""
An Iterable of BuildInfo dicts
"""


DecoratedBuildInfos = Iterable[DecoratedBuildInfo]
"""
An Iterable of DecoratedBuildInfo dicts
"""


BuildSpec = Union[int, str, BuildInfo]
"""
An indicator for a build in cases where the build may be
communicated as its ID, its NVR, or as an already-loaded BuildInfo
"""


class DecoratedArchiveInfo(ArchiveInfo):
    pass


DecoratedArchiveInfos = Iterable[DecoratedArchiveInfo]


class MavenArchiveInfo(ArchiveInfo):
    """
    An ArchiveInfo with additional fields representing the maven GAV
    (Group, Artifact, Version)
    """

    artifact_id: str
    """ The maven artifact's name """

    group_id: str
    """ The maven artifact's group """

    version: str
    """ The maven artifact's version """


MavenArchiveInfos = Iterable[MavenArchiveInfo]


PathSpec = Union[str, PathInfo]
"""

"""


class RPMInfo(TypedDict):
    """
    Data representing a koji RPM. These are typically obtained via the
    ``listRPMs`` XMLRPC call, or from the `kojismokydingo.as_rpminfo`
    function
    """

    arch: str
    """ The RPM's architecture, eg. 'src' or 'x86_64' """

    build_id: int
    """ The ID of the build owning this RPM """

    buildroot_id: int
    """ The buildroot used by the task which produced this RPM """

    buildtime: int
    """ UTC timestamp of the time that this RPM was produced """

    epoch: str
    """ The RPM's epoch field, or None if not defined """

    external_repo_id: int
    """ The external repo ID for this RPM record, or 0 if the RPM was
    built in this koji instance rather than being a reference to an
    external repository """

    external_repo_name: str
    """ name identifying the repo that this RPM came from, or 'INTERNAL'
    if built in this koji instance """

    extra: dict
    """ Optional extra data """

    id: int
    """ The internal ID for this RPM """

    metadata_only: bool

    name: str
    """ The RPM's name field """

    nvr: str
    """ The NVR (Name Version and Release) of the RPM """

    payloadhash: str
    """ The MD5 in hex of the RPM's payload (the content past the
    headers) """

    release: str
    """ The RPM's release field """

    size: int
    """ The file size of the unsigned copy of the RPM """

    version: str
    """ The RPM's version field """


RPMInfos = Iterable[RPMInfo]


RPMSpec = Union[int, str, RPMInfo]
"""
Ways to indicate an RPM to `as_rpminfo`
"""


class RPMSignature(TypedDict):
    rpm_id: int

    sigkey: str

    sighash: str


class DecoratedRPMInfo(RPMInfo):
    sigkey: str


DecoratedRPMInfos = Iterable[DecoratedRPMInfo]


class WindowsArchiveInfo(ArchiveInfo):
    platforms: List[str]


WindowsArchiveInfos = Iterable[WindowsArchiveInfo]


class ImageArchiveInfo(ArchiveInfo):
    pass


ImageArchiveInfos = Iterable[ImageArchiveInfo]


class HostInfo(TypedDict):
    """
    Data representing a koji host. These are typically obtained via the
    ``getHost`` XMLRPC call
    """

    arches: str
    """ space-separated list of architectures this host can handle """

    capacity: float
    """ maximum capacity for tasks """

    comment: str
    """ text describing the current status or usage """

    description: str
    """ text describing this host """

    enabled: bool
    """ whether this host is configured by the hub to take tasks """

    id: int
    """ internal identifier """

    name: str
    """ user name of this host's account, normally FQDN. """

    ready: bool
    """ whether this host is reporting itself as active and prepared to
    accept tasks """

    task_load: float
    """ the load of currently running tasks on the host. Compared with the
    capacity and a given task's weight, this can determine whether a
    task will 'fit' on the host """

    user_id: int
    """ the user ID of this host's account. Hosts have a user account of
    type HOST, which is how they authenticate with the hub """


HostSpec = Union[int, str, HostInfo]
"""

"""


class DecoratedHostInfo(HostInfo):
    last_update: datetime
    """ The last time that a host checked in with an update """


DecoratedHostInfos = Iterable[DecoratedHostInfo]


class UserStatus(IntEnum):
    """
    Valid values for the ``'status'`` item of a `UserInfo` dict
    """

    NORMAL = USER_STATUS['NORMAL']
    """ account is enabled """

    BLOCKED = USER_STATUS['BLOCKED']
    """
    account is blocked. May not call XMLRPC endpoints requiring
    authentication
    """


class UserType(IntEnum):
    """
    Valid values for the ``'usertype'`` item of a `UserInfo` dict
    """

    NORMAL = USERTYPES['NORMAL']
    """ Account is a normal user """

    HOST = USERTYPES['HOST']
    """ Account is a build host """

    GROUP = USERTYPES['GROUP']
    """ Account is a group """


class UserInfo(TypedDict):
    """
    Data representing a koji user account. These are typically
    obtained via the ``getUser`` XMLRPC call, or the
    ``kojismokydingo.as_userinfo`` function.
    """

    id: int
    """ internal identifer """

    krb_principal: str
    """ kerberos principal associated with the user. Only used in koji
    before 1.19 """

    krb_principals: List[str]
    """ list of kerberos principals associated with the user. Used in koji
    from 1.19 onwards. """

    name: str
    """ the username """

    status: UserStatus
    """ status of the account """

    usertype: UserType
    """ type of the account """


UserSpec = Union[int, str, UserInfo]
"""
Acceptable ways to specify a user, either by a UserInfo dict, a
username str, or a user's int ID
"""


class CGInfo(TypedDict):
    """
    Data representing a koji Content Generator. A dict of these are
    typically obtained via the ``listCGs`` XMLRPC call, mapping their
    friendly names to the CGInfo structure
    """

    id: int
    """ internal identifier """

    users: List[str]
    """ list of account names with access to perform CGImports using
    this content generator """


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
    create_ts: Union[int, float]
    create_date: datetime


class PermInfo(TypedDict):
    id: int
    name: str
    users: List[PermUser]


PermSpec = Union[int, str]
"""
a permission's ID or name
"""


class DecoratedUserInfo(UserInfo):

    permissions: List[PermInfo]

    content_generators: List[NamedCGInfo]

    members: List[str]


class TargetInfo(TypedDict):

    build_tag_name: str


TargetInfos = Iterable[TargetInfo]


TargetSpec = Union[int, str, TargetInfo]
"""
An indicator for a target in cases where it may be communicated by
its ID, its name, or an already-loaded TargetInfo
"""


class TagInfo(TypedDict):

    id: int

    name: str

    extra: Dict[str, str]


TagInfos = Iterable[TagInfo]


TagSpec = Union[int, str, TagInfo]
"""
An indicator for a tag in cases where it may be communicated by
its ID, its name, or as an already-loaded TagInfo
"""


class TagInheritanceEntry(TypedDict):
    priority: int
    parent_id: int


TagInheritance = List[TagInheritanceEntry]


class DecoratedTagExtra(TypedDict):
    name: str
    value: str
    blocked: bool
    tag_name: str
    tag_id: int


DecoratedTagExtras = Dict[str, DecoratedTagExtra]


class TaskInfo(TypedDict):
    id: int
    method: str
    request: Any


TaskSpec = Union[int, TaskInfo]
"""
task ID or TaskInfo dict
"""


HubVersionSpec = Union[str, Tuple[int, ...]]
"""
a koji version requirement, specified as either a string or tuple of ints

  * ``"1.25"``
  * ``(1, 25)``
"""


KeySpec = Union[Callable[[Any], Any], Any]


class GOptions:
    topurl: str
    weburl: str
    profile: str


#
# The end.
