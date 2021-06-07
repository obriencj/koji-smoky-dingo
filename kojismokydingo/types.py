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
from koji import BUILD_STATES
from typing import Iterable, List, Optional, Union

try:
    from typing import TypedDict

except ImportError:
    # Python < 3.8 doesn't have TypedDict yet, need to pull it in from
    # the typing_extensions backport instead.
    from typing_extensions import TypedDict


__all__ = (
    "ArchiveChecksum",
    "ArchiveInfo",
    "ArchiveInfos",
    "BuildInfo",
    "BuildInfos",
    "BuildState",
    # "HostInfo",
    "MavenArchiveInfo",
    "RPMInfo",
    # "TagInfo",
    # "TargetInfo",
    # "TaskInfo",
    # "UserInfo",
)


class ArchiveChecksum(IntEnum):
    MD5 = 0
    SHA1 = 1
    SHA256 = 2


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

    checksum_type: int
    """ type of checksum, see `ArchiveChecksum` """

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


class BuildState(IntEnum):
    """
    Values for a BuildInfo's state.

    * BUILDING = 0
    * COMPLETE = 1
    * DELETED = 2
    * FAILED = 3
    * CANCELED = 4

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


BuildInfos = Iterable[BuildInfo]
"""
An Iterable of BuildInfo dicts
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


class WindowsArchiveInfo(ArchiveInfo):
    platforms: List[str]


#
# The end.
