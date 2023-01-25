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
    AUTHTYPE_NORMAL, AUTHTYPE_KERB, AUTHTYPE_SSL, AUTHTYPE_GSSAPI,
    BR_STATES, BR_TYPES, BUILD_STATES, CHECKSUM_TYPES, REPO_STATES,
    TASK_STATES, USERTYPES, USER_STATUS,
    PathInfo, )
from optparse import Values
from typing import (
    Any, Callable, Dict, Iterable, List,
    Optional, Tuple, Union, )


try:
    from typing import TypedDict

except ImportError:
    # Python < 3.8 doesn't have TypedDict yet, need to pull it in from
    # the typing_extensions backport instead.
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
    "DecoratedBuildInfo",
    "DecoratedHostInfo",
    "DecoratedHostInfos",
    "DecoratedTagExtra",
    "DecoratedTagExtras",
    "GOptions",
    "HistoryEntry",
    "HostInfo",
    "HubVersionSpec",
    "KeySpec",
    "NamedCGInfo",
    "PackageInfo",
    "PackageSpec",
    "PathSpec",
    "PermInfo",
    "PermSpec",
    "RepoInfo",
    "RepoState",
    "RPMInfo",
    "RPMInfos",
    "RPMSignature",
    "RPMSpec",
    "SearchResult",
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
    "UserInfo",
    "UserSpec",
    "UserStatus",
    "UserStatistics",
    "UserType",
)


class AuthType(IntEnum):
    """
    Authentication method types

    Normally only used in the `kojismokydingo.types.UserInfo` dict
    when obtained via the ``getLoggedInUser`` XMLRPC call.
    """

    GSSAPI = AUTHTYPE_GSSAPI
    """ user authenticated via GSSAPI """

    KERB = AUTHTYPE_KERB
    """ user authenticated via a Kerberos ticket """

    NORMAL = AUTHTYPE_NORMAL
    """ user authenticated via password """

    SSL = AUTHTYPE_SSL
    """ user authenticated via an SSL certificate """


class BuildrootState(IntEnum):
    """
    Values for a BuildrootInfo's br_state

    See `koji.BR_STATES`
    """

    INIT = BR_STATES['INIT']
    WAITING = BR_STATES['WAITING']
    BUILDING = BR_STATES['BUILDING']
    EXPIRED = BR_STATES['EXPIRED']


class BuildrootType(IntEnum):
    """
    Values for a BuildrootInfo's br_type

    See `koji.BR_TYPES`
    """

    STANDARD = BR_TYPES['STANDARD']
    EXTERNAL = BR_TYPES['EXTERNAL']


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


class ChecksumType(IntEnum):
    """
    Supported checksum types
    """

    MD5 = CHECKSUM_TYPES['md5']
    SHA1 = CHECKSUM_TYPES['sha1']
    SHA256 = CHECKSUM_TYPES['sha256']


class RepoState(IntEnum):
    INIT = REPO_STATES['INIT']
    READY = REPO_STATES['READY']
    EXPIRED = REPO_STATES['DELETED']
    PROBLEM = REPO_STATES['PROBLEM']


class TaskState(IntEnum):
    FREE = TASK_STATES['FREE']
    OPEN = TASK_STATES['OPEN']
    CLOSED = TASK_STATES['CLOSED']
    CANCELED = TASK_STATES['CANCELED']
    ASSIGNED = TASK_STATES['ASSIGNED']
    FAILED = TASK_STATES['FAILED']


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

    artifact_id: str
    """ Only present on maven archives. The maven artifact's name """

    group_id: str
    """ Only present on maven archives. The maven artifact's group """

    version: str
    """ Only present on maven archives. The maven artifact's version """

    platforms: List[str]
    """ Only present on Windows archives """

    relpath: str
    """ Only present on Windows archives """

    flags: str
    """ Only present on Windows archives """

    arch: str
    """ Only present on Image archives """


ArchiveInfos = Iterable[ArchiveInfo]
""" An Iterable of ArchiveInfo dicts """


class DecoratedArchiveInfo(ArchiveInfo):
    filepath: str


DecoratedArchiveInfos = Iterable[DecoratedArchiveInfo]


ArchiveSpec = Union[int, str, ArchiveInfo]
"""
An archive ID, filename, or info dict
"""


class ArchiveTypeInfo(TypedDict):

    description: str
    """ short title of the type """

    extensions: str
    """ space separated extensions for this type """

    id: int
    """ the internal ID of the archive type """

    name: str
    """ the name of the archive type """


class BuildrootInfo(TypedDict):
    arch: str
    br_type: BuildrootType

    cg_id: Optional[int]
    cg_name: Optional[str]
    cg_version: Optional[str]

    container_arch: str
    container_type: str

    create_event_id: int
    create_event_time: str
    create_ts: float

    extra: Optional[dict]

    host_arch: Optional[str]
    host_id: int
    host_name: str
    host_os: Optional[str]

    id: int

    repo_create_event_id: int
    repo_create_event_time: str

    repo_id: int
    repo_state: RepoState

    retire_event_id: int
    retire_event_time: str
    retire_ts: float

    state: BuildrootState

    tag_id: int
    tag_name: str

    task_id: int

    workdir: str


class BuildInfo(TypedDict):
    """
    Data representing a koji build. These are typically obtained via
    the ``getBuild`` XMLRPC call, or from the
    `kojismokydingo.as_buildinfo` function.
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

    completion_ts: float
    """ UTC timestamp indicating when this build was completed """

    creation_event_id: int
    """ koji event ID at the creation of this build record """

    creation_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this build
    record was created """

    creation_ts: float
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
    start_ts: float

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

    maven_group_id: Optional[str]
    """ only present on Maven builds which have been loaded with type
    information """

    maven_artifact_id: Optional[str]
    """ only present on Maven builds which have been loaded with type
    information """

    maven_version: Optional[str]
    """ only present on Maven builds which have been loaded with type
    information """

    platform: Optional[str]
    """ only present on Windows builds which have been loaded with type
    information """


class DecoratedBuildInfo(BuildInfo):

    archive_btype_names: List[str]
    archive_btype_ids: List[int]

    archive_cg_names: List[str]
    archive_cg_ids: List[int]


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


class BTypeInfo(TypedDict):
    id: int
    """ the internal ID of the btype """

    name: str
    """ the name of the btype """


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
    """
    Data representing an RPM signature in koji. Obtained via the
    ``queryRPMSigs`` XMLRPC API or from the
    `kojismokydingo.bulk_load_rpm_sigs` function.
    """

    rpm_id: int

    sigkey: str

    sighash: str


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


class HostInfo(TypedDict):
    """
    Data representing a koji host. These are typically obtained via the
    ``getHost`` XMLRPC call
    """

    arches: str
    """ space-separated list of architectures this host can handle """

    capacity: float
    """ maximum capacity for tasks, using the sum of the task weight
    values """

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
Acceptable ways to specify a host
"""


class DecoratedHostInfo(HostInfo):
    last_update: datetime
    """ The last time that a host checked in with an update """


DecoratedHostInfos = Iterable[DecoratedHostInfo]


class UserInfo(TypedDict):
    """
    Data representing a koji user account. These are typically
    obtained via the ``getUser`` or ``getLoggedInUser`` XMLRPC calls,
    or the ``kojismokydingo.as_userinfo`` function.
    """

    authtype: AuthType
    """ Only present from the ``getLoggedInUser`` call """

    id: int
    """ internal identifer """

    krb_principal: str
    """ kerberos principal associated with the user. Only used in koji
    before 1.19 or when using the ``getLoggedInUser`` call. """

    krb_principals: List[str]
    """ list of kerberos principals associated with the user. Used in koji
    from 1.19 onwards. """

    name: str
    """ the username """

    status: UserStatus
    """ status of the account. not present for members from the
    ``getGroupMembers`` call. """

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
    create_ts: float
    create_date: datetime


class PermInfo(TypedDict):
    id: int
    name: str


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

    members: List[UserInfo]
    """ membership if user is a group """

    statistics: Optional[UserStatistics]
    """ user's interaction statistics """


class RepoInfo(TypedDict):
    """
    Data representing a koji build tag's repository. These are
    typically obtained via the ``getRepo`` or ``repoInfo`` XMLRPC
    calls, or from the `kojismokydingo.as_repoinfo` function.
    """

    create_event: int
    """ koji event ID representing the point that the repo's tag
    configuration was snapshot from. Note that this doesn't always
    correlate to the creation time of the repo -- koji has the ability to
    generate a repository based on older events """

    create_ts: float
    """ UTC timestamp indicating when this repo was created """

    creation_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this repo
    was created """

    dist: bool
    """ whether this is a dist-repo or not """

    id: int
    """ internal ID for this repository """

    state: RepoState
    """ the current state of this repository """

    tag_id: int
    """ ID of the tag from which this repo was generated. This value is not
    present in the output of the ``getRepo`` XMLRPC call as it is presumed
    that the caller already knows the tag's identity """

    tag_name: str
    """ name of the tag from which this repo was generated.  This value is
    not present in the output of the ``getRepo`` XMLRPC call as it is
    presumed that the caller already knows the tag's identity """

    task_id: int
    """ ID of the task which generated this repository """


RepoSpec = Union[int, RepoInfo, str, 'TagInfo']
"""
`kojismokydingo.as_repoinfo`
"""


class TargetInfo(TypedDict):
    """
    Data representing a koji build target. Typically obtained via the
    ``getBuildTarget`` or ``getBuildTargets`` XMLRPC calls, or the
    `kojismokydingo.as_targetinfo` function.
    """

    build_tag: int
    """ internal ID of the target's build tag """

    build_tag_name: str
    """ name of the target's build tag """

    dest_tag: int
    """ internal ID of the target's destination tag """

    dest_tag_name: str
    """ name of the target's destination tag """

    id: int
    """ internal ID of this build target """

    name: str
    """ name of this build target """


TargetInfos = Iterable[TargetInfo]


TargetSpec = Union[int, str, TargetInfo]
"""
An indicator for a target in cases where it may be communicated by
its ID, its name, or an already-loaded TargetInfo
"""


class TagInfo(TypedDict):
    """
    Data representing a koji tag. Typically obtained via the
    ``getTag`` XMLRPC call, or the `kojismokydingo.as_taginfo` and
    `kojismokydingo.bulk_load_tags` functions.
    """

    arches: str
    """ space-separated list of architectures, or None """

    extra: Dict[str, str]
    """ inheritable additional configuration data """

    id: int
    """ internal ID of this tag """

    locked: bool
    """ when locked, a tag will protest against having addtional builds
    associated with it """

    maven_include_all: bool
    """ whether this tag should use the alternative maven-latest logic
    (including multiple builds of the same package name) when inherited
    by the build tag of a maven-enabled target """

    maven_support: bool
    """ whether this tag should generate a maven repository when it is
    the build tag for a target """

    name: str

    perm: str
    """ name of the required permission to associate builds with this tag,
    or None """

    perm_id: int
    """ ID of the required permission to associate builds with this tag,
    or None """


TagInfos = Iterable[TagInfo]


TagSpec = Union[int, str, TagInfo]
"""
An indicator for a tag in cases where it may be communicated by
its ID, its name, or as an already-loaded TagInfo
"""


class TagInheritanceEntry(TypedDict):
    """
    Data representing a single inheritance element. A list of these
    represents the inheritance data for a tag. Typically obtained via
    the ``getFullInheritance`` XMLRPC call.
    """

    child_id: int
    """ the ID of the child tag in the inheritance link. The child tag
    inherits from the parent tag """

    currdepth: int
    """ only present from the ``getFullInheritance`` call. The inheritance
    depth this link occurs at. A depth of 1 indicates that the child
    tag would be the one originally queried for its inheritance tree
    """

    filter: list
    """ only present from the ``getFullInheritance`` call. """

    intransitive: bool
    """ if true then this inheritance link would not be inherited. ie.
    this link only appears at a depth of 1, and is otherwise omitted. """

    maxdepth: int
    """ additional parents in the inheritance tree from this link are only
    considered up to this depth, relative from the link's current
    depth.  A maxdepth of 1 indicates that only the immediate parents
    will be inherited. A maxdepth of 0 indicates that the tag and none
    of its parents will be inherited. A value of None indicates no
    restriction. """

    name: str
    """ the parent tag's name """

    nextdepth: int
    """ only present from the ``getFullInheritance`` call. """

    noconfig: bool
    """ if True then this inheritance link does not include tag
    configuration data, such as extras and groups """

    parent_id: int
    """ the parent tag's internal ID """

    pkg_filter: str
    """ a regex indicating which package entries may be inherited. If empty,
    all packages are inherited """

    priority: int
    """ the inheritance link priority, which provides an ordering for
    links at the same depth with the same child tag (ie. what order
    the parent links for a given tag are processed in). Lower
    priorities are processed first. """


TagInheritance = List[TagInheritanceEntry]
"""
As returned by the ``getInheritanceData`` and
``getFullInheritance`` XMLRPC calls. A list of inheritance elements
for a tag.
"""


class DecoratedTagExtra(TypedDict):
    blocked: bool
    name: str
    tag_name: str
    tag_id: int
    value: str


DecoratedTagExtras = Dict[str, DecoratedTagExtra]


class PackageInfo(TypedDict):
    """
    ``getPackage`` XMLRPC call.
    """

    id: int
    """
    the internal ID for this package
    """

    name: str
    """
    the package name
    """


PackageSpec = Union[int, str, PackageInfo]
"""
`kojismokydingo.as_packageinfo`
"""


class TagPackageInfo(TypedDict):
    """
    ``listPackages`` XMLRPC call.
    """

    blocked: bool
    """ if True this entry represents a block """

    extra_arches: str
    """ additional architectures, separated by spaces """

    owner_id: int
    """ ID of the user who is the owner of the package for this tag """

    owner_name: str
    """ name of the user who is the owner of the package for this tag """

    package_id: int
    """ ID of the package """

    package_name: str
    """ name of the package """

    tag_id: int
    """ ID of the package listing's tag """

    tag_name: str
    """ name of the package listing's tag """


class TagGroupPackage(TypedDict):
    basearchonly: str
    blocked: bool
    group_id: int
    package: str
    requires: str
    tag_id: int
    type: str


class TagGroupReq(TypedDict):
    blocked: bool
    group_id: int
    is_metapkg: bool
    name: str
    req_id: int
    tag_id: int
    type: str


class TagGroupInfo(TypedDict):
    """
    ``getTagGroups`` XMLRPC call
    """

    biarchonly: bool
    blocked: bool
    description: str
    display_name: str
    exported: bool
    group_id: int
    grouplist: List[TagGroupReq]
    is_default: bool
    langonly: str
    name: str
    packagelist: List[TagGroupPackage]
    tag_id: int
    uservisible: bool


class TaskInfo(TypedDict):
    """
    ``getTaskInfo`` XMLRPC call or `kojismokydingo.as_taskinfo` function
    """

    arch: str
    """ task architecture, or 'noarch' """

    awaited: Union[bool, None]
    """ True if this task is currently being waiting-for by its parent
    task.  False if this task is no longer being waited-for. None if
    the task was never waited-for. """

    channel_id: int
    """ internal ID of the channel from which a host will be selected to
    take this task """

    completion_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this task
    was completed, or None if not completed """

    completion_ts: float
    """ UTC timestamp indicating when this task was completed, or None if
    not completed """

    create_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this task
    was created """

    create_ts: float
    """ UTC timestamp indicating when this task was created """

    host_id: int
    """ host which has taken this task, or None """

    id: int
    """ internal task ID """

    label: str
    """ task label, or None """

    method: str
    """ task method, indicates the type of work to be done """

    owner: int
    """ ID of the user that initiated this task """

    parent: int
    """ ID of the parent task, or None """

    priority: int

    start_time: str
    """ ISO-8601 formatted UTC datetime stamp indicating when this task
    was started by a host, or None if not yet started """

    start_ts: float
    """ UTC timestamp indicating when this task was started by a host, or
    None if not yet started """

    state: TaskState
    """ the current state of this task """

    waiting: Union[bool, None]
    """ True if this task is currently waiting for any of its subtasks to
    complete. False if this task is not waiting, or None if the task
    never needed to wait. """

    weight: float
    """ value which ascribes the general resources needed to perform this
    task. hosts have a limit to the number of resources which can be used
    to run tasks in parallel """

    request: List[Any]
    """ The task request info. Only present when the request parameter to
    the ``getTaskInfo`` call is `True`. Note that the `as_taskinfo`
    function does set that parameter to True. """


TaskSpec = Union[int, TaskInfo]
"""
task ID or TaskInfo dict
"""


class ChannelInfo(TypedDict):
    id: int
    """ internal channel ID """

    name: str
    """ channel name """


ChannelSpec = Union[int, str, ChannelInfo]


class SearchResult(TypedDict):
    """ as returned by the ``search`` XMLRPC call """

    id: int
    """ result ID """

    name: str
    """ result name """


HubVersionSpec = Union[str, Tuple[int, ...]]
"""
a koji version requirement, specified as either a string or tuple of ints

  * ``"1.25"``
  * ``(1, 25)``
"""


KeySpec = Union[Callable[[Any], Any], Any]
"""
a key specifier, used as either an index/item lookup on objects, or a
unary callable which returns the desired field.

Typically non callable keyspec values are converted into an itemgetter
using that value.
"""


class GOptions(Values):
    """
    Represents the koji client configuration options as provided by the
    baseline koji CLI.

    `Values` instances with these fields are fed to
    `kojismokydingo.cli.SmokyDingo` instances via their ``__call__``
    handlers.

    Note that koji uses the `optparse` package, while koji smoky dingo
    uses the `argparse` package.

    Returned by the ``get_options`` function from within the koji CLI
    utility, which cannot be imported normally. Default values for
    these are pulled from the profile configuration if unspecified as
    base CLI arguments.
    """

    authtype: str
    cert: str = None
    debug: bool = False
    force_auth: bool = False
    keytab: str = None
    noauth: bool = False
    password: str = None
    plugin_paths: str = None
    principal: str = None
    profile: str
    quiet: bool = False
    runas: str = None
    server: str
    skip_main: bool = False
    topdir: str
    topurl: str
    user: str
    weburl: str


HistoryEntry = Tuple[int, str, bool, Dict[str, Any]]


#
# The end.
