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


from enum import IntEnum
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from inspect import currentframe
from os import getenv
from os.path import basename
from koji import (
    BUILD_STATES, CHECKSUM_TYPES, USERTYPES, USER_STATUS,
    PathInfo, )
from typing import Iterable, List, Optional, Union


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
    "BuildInfo",
    "BuildInfos",
    "BuildSpec",
    "BuildState",
    "ChecksumType",
    "HostInfo",
    "MavenArchiveInfo",
    "PathSpec",
    "PermInfo",
    "PermSpec",
    "RPMInfo",
    "RPMSpec",
    "TagInfo",
    "TagSpec",
    "TargetInfo",
    "TargetSpec",
    "TaskInfo",
    "TaskSpec",
    "UserInfo",
    "UserSpec",

    "merge_annotations",
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

    extra: Optional[dict]
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

    cg_id: Optional[int]
    """ The ID of the content generator which has reserved or produced
    this build """

    cg_name: Optional[str]
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

    epoch: Optional[str]
    """ epoch of this build, or None if unspecified. This field is
    typically only used for RPM builds which have specified an epoch
    in their spec. """

    extra: Optional[dict]
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
    source: Optional[str]
    start_time: Optional[str]
    start_ts: Optional[Union[int, float]]

    state: int
    """ state of the build, see `BuildState` """

    task_id: Optional[int]

    version: str
    """ version portion of the NVR for the build """

    volume_id: int
    """ ID of the storage volume that the archives for this build will be
    stored on """

    volume_name: str
    """ name of the storage that the archives for this build will be
    stored on """


class MavenBuildInfo(BuildInfo):
    pass


class DecoratedBuildInfo(BuildInfo):
    pass


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

    epoch: Optional[str]
    """ The RPM's epoch field, or None if not defined """

    external_repo_id: int
    """ The external repo ID for this RPM record, or 0 if the RPM was
    built in this koji instance rather than being a reference to an
    external repository """

    external_repo_name: str
    """ name identifying the repo that this RPM came from, or 'INTERNAL'
    if built in this koji instance """

    extra: Optional[dict]
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


RPMSpec = Union[int, str, RPMInfo]
"""
Ways to indicate an RPM to `as_rpminfo`
"""


class WindowsArchiveInfo(ArchiveInfo):
    platforms: List[str]


class HostInfo(TypedDict):
    """
    Data representing a koji host. These are typically obtained via the
    ``getHost`` XMLRPC call
    """

    arches: str
    """ space-separated list of architectures this host can handle """

    capacity: float
    """ maximum capacity for tasks """

    comment: Optional[str]
    """ text describing the current status or usage """

    description: Optional[str]
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

    krb_principal: Optional[str]
    """ kerberos principal associated with the user. Only used in koji
    before 1.19 """

    krb_principals: Optional[List[str]]
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


class PermInfo(TypedDict):
    pass


PermSpec = Union[int, str]
"""
a permission's ID or name
"""


class DecoratedUserInfo(UserInfo):

    permissions: List[PermInfo]

    content_generators: List[NamedCGInfo]

    members: Optional[List[str]]


class TargetInfo(TypedDict):
    pass


TargetSpec = Union[int, str, TargetInfo]
"""
An indicator for a target in cases where it may be communicated by
its ID, its name, or an already-loaded TargetInfo
"""


class TagInfo(TypedDict):
    pass


TagSpec = Union[int, str, TagInfo]
"""
An indicator for a tag in cases where it may be communicated by
its ID, its name, or as an already-loaded TagInfo
"""


class TaskInfo(TypedDict):
    pass


TaskSpec = Union[int, TaskInfo]
"""
task ID or TaskInfo dict
"""


# Below this point are functions to asssist in merging .pyi type stubs
# into the actual .py modules at runtime. This is primarily used to
# allow sphinx to see the typing annotations without having to embed
# them directly in the real modules.

# We'll use the env var KSD_MERGE_PYI as a sentinel for the
# merge_signatures function. If not set to some agreeable value we
# won't perform the signature merging. We can turn it on during docs
# generation in order to get the typing data in our documentation, and
# then avoid it for normal runtime operation.
KSD_MERGE_PYI = getenv("KSD_MERGE_PYI", "").lower() in ("1", "true", "yes")


def _load_pyi(spec):
    """
    Given a module spec, import the matching .pyi as a separate module
    """

    # the base filename from the module we're loading stubs for
    py_file = basename(spec.origin)

    # we'll look for a resource in the same package with this filename
    pyi_file = py_file + "i"
    pyi_path = spec.loader.resource_path(pyi_file)

    # we'll pretend the .pyi file is a module named after the original
    # with a suffix _pyi_
    pyi_name = spec.name + "_pyi_"

    # load the stubs into a new module
    pyi_loader = SourceFileLoader(pyi_name, pyi_path)
    pyi_spec = spec_from_loader(pyi_name, pyi_loader)
    pyi_mod = module_from_spec(pyi_spec)
    pyi_spec.loader.exec_module(pyi_mod)

    return pyi_mod


def _merge_annotations(glbls, pyi_glbls):
    """
    Merge the annotations from pyi_glbls into glbls. Recurses into
    type declarations.
    """

    for key, pyi_thing in pyi_glbls.items():
        if key not in glbls or key.startswith("_"):
            continue

        thing = glbls[key]
        thing_anno = getattr(thing, '__annotations__', None)

        pyi_anno = getattr(pyi_thing, '__annotations__', None)

        if thing_anno is None:
            if pyi_anno is not None:
                thing.__annotations__ = pyi_anno

        elif pyi_anno is not None:
            thing_anno.update(pyi_anno)

        if isinstance(thing, type):
            # recur down type definitions in order to get annotations
            # for methods
            _merge_annotations(vars(thing), vars(pyi_thing))


def merge_annotations(force=False):
    """
    Merge PEP-0484 stub files into the calling module's annotations if
    the `KSD_MERGE_PYI` global is True. The value of `KSD_MERGE_PYI` is
    set at load time based on an environment variable of the same
    name.

    The .pyi file must be in the same path as the original .py file.

    :param force: perform annotation merging even if KSD_MERGE_PYI is
      not True
    """

    if not (force or KSD_MERGE_PYI):
        return

    back = currentframe().f_back
    assert back is not None, "merge_signatures invoked without parent frame"

    glbls = back.f_globals
    spec = glbls.get('__spec__')
    assert spec is not None, "merge_signatures invoked without module spec"

    # find and load the .pyi annotations as a module
    pyi_mod = _load_pyi(spec)

    # merge the annotations from the .pyi module globals into glbls
    _merge_annotations(glbls, vars(pyi_mod))


#
# The end.
