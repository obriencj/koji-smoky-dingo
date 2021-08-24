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
Typing annotations for the koji XMLRPC API
"""


from typing import (
    Any, Dict, List, Optional, Tuple, Union, )

from kojismokydingo.types import (
    ArchiveInfo, BuildInfo, ImageBuildInfo, ImageArchiveInfo,
    MavenArchiveInfo,
    MavenBuildInfo, RPMInfo, TagInfo, WindowsArchiveInfo,
    WindowsBuildInfo, )


BUILD_STATES: Dict[str, int]
CHECKSUM_TYPES: Dict[str, int]
REPO_STATES: Dict[str, int]
TASK_STATES: Dict[str, int]
USERTYPES: Dict[str, int]
USER_STATUS: Dict[str, int]


class Fault:
    def __init__(
            self,
            faultCode: int,
            faultString: str,
            **extra: Any):
        ...


class GenericError(Exception):
    faultCode: int
    fromFault: bool


class ParameterError(GenericError):
    ...


class PathInfo:
    def __init__(
            self,
            topdir: str = None):
        ...

    def build(
            self,
            build: BuildInfo) -> str:
        ...

    def build_logs(
            self,
            build: BuildInfo) -> str:
        ...

    def distrepo(
            self,
            repo_id: int,
            tag: TagInfo,
            volume: str = None) -> str:
        ...

    def filepath(
            self,

    def imagebuild(
            self,
            build: ImageBuildInfo) -> str:
        ...

    def mavenbuild(
            self,
            build: MavenBuildInfo) -> str:
        ...

    def mavenfile(
            self,
            maveninfo: MavenArchiveInfo) -> str:
        ...

    def rpm(
            self,
            rpminfo: RPMInfo) -> str:
        ...

    def signed(
            self,
            rpminfo: RPMInfo,
            sigkey: str) -> str:
        ...

    def typedir(
            self,
            build: BuildInfo,
            btype: str) -> str:
        ...

    def winbuild(
            self,
            build: WindowsBuildInfo) -> str:
        ...

    def winfile(
            self,
            wininfo: WindowsArchiveInfo) -> str:
        ...


TODO = Any
""" this type alias is a placeholder for cases where I am unsure what
the actual type of a parameter is """


class ClientSession:

    baseurl: str
    opts: Dict[str, Any]
    multicall: bool

    def __init__(
            self,
            baseurl: str,
            opts: Optional[Dict[str, Any]] = None,
            sinfo: Optional[Dict[str, Any]] = None):
        ...

    def getBuild(
            self,
            buildInfo: Union[int, str],
            strict: bool = False) -> BuildInfo:
        ...

    def getBuildType(
            self,
            buildInfo: Union[int, str],
            strict: bool = False) -> Dict[str, dict]:
        ...

    def getBuildroot(
            self,
            buildrootID: int,
            strict: bool = False) -> BuildrootInfo:
        ...

    def getLatestBuilds(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            package: Optional[Union[int, str]] = None,
            type: Optional[str] = None) -> List[BuildInfo]:
        ...

    def getTag(
            self,
            taginfo: Union[int, str],
            strict: bool = False,
            event: Optional[int] = None,
            blocked: bool = False) -> TagInfo:
        ...

    def getTaskInfo(
            self,
            task_id: int,
            request: bool = False,
            strict: bool = False) -> TaskInfo:
        ...

    def listArchives(
            self,
            buildID: Optional[int] = None,
            buildrootID: Optional[int] = None,
            componentBuildrootID: Optional[int] = None,
            hostID: Optional[int] = None,
            type: Optional[str] = None,
            filename: Optional[str] = None,
            size: Optional[int] = None,
            checksum: Optional[str] = None,
            typeInfo: TODO = None,
            queryOpts: Optional[Dict] = None,
            imageID: Optional[int] = None,
            archiveID: Optional[int] = None,
            strict: bool = False) -> Union[List[ArchiveInfo],
                                           List[ImageArchiveInfo],
                                           List[MavenArchiveInfo],
                                           List[WindowsArchiveInfo]]:
        ...


    def multiCall(
            self,
            strict: bool = False,
            batch: Optional[int] = None) -> List:
        ...


def convertFault(fault: Fault) -> GenericError:
    ...


def read_config(
        profile_name: str,
        user_config: Optional[str] = None) -> Dict[str, Any]:
    ...


#
# The end.
