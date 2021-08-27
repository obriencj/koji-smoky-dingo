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
Koji - type stubs

Typing annotations stub for the parts of koji used by koji smoky
dingo. In particular there are annotations for the virtual XMLRPC
methods on the ClientSession class which should help check that the
calls are being used correctly.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from typing import (
    Any, Dict, List, Optional, TypedDict, Tuple, Union, )

from kojismokydingo.types import (
    ArchiveInfo, ArchiveTypeInfo, BuildInfo, BuildrootInfo, BTypeInfo,
    ChannelInfo, CGInfo, HostInfo, PermInfo, RepoInfo, RepoState,
    RPMInfo, RPMSignature, SearchResult, TagInfo, TagGroup,
    TagInheritance, TagPackageInfo, TargetInfo, TaskInfo, UserInfo, )


BR_STATES: Dict[str, int]
BR_TYPES: Dict[str, int]
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


class FaultInfo(TypedDict):
    faultCode: int
    faultString: str


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

    def imagebuild(
            self,
            build: BuildInfo) -> str:
        ...

    def mavenbuild(
            self,
            build: BuildInfo) -> str:
        ...

    def mavenfile(
            self,
            maveninfo: ArchiveInfo) -> str:
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
            build: BuildInfo) -> str:
        ...

    def winfile(
            self,
            wininfo: ArchiveInfo) -> str:
        ...


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

    def createTag(
            self,
            name: str,
            parent: Optional[Union[int, str]] = None,
            arches: Optional[str] = None,
            perm: Optional[str] = None,
            locked: bool = False,
            maven_support: bool = False,
            maven_include_all: bool = False,
            extra: Optional[Dict[str, str]] = None) -> int:
        pass

    def editTag2(
            self,
            taginfo: Union[int, str],
            **kwargs):
        ...

    def getAllPerms(self) -> List[PermInfo]:
        ...

    def getArchive(
            self,
            archive_id: int,
            strict: bool = False) -> ArchiveInfo:
        ...

    def getArchiveType(
            self,
            filename: Optional[str] = None,
            type_name: Optional[str] = None,
            type_id: Optional[int] = None,
            strict: bool = False) -> ArchiveTypeInfo:
        ...

    def getArchiveTypes(self) -> List[ArchiveTypeInfo]:
        ...

    def getBuild(
            self,
            buildInfo: Union[int, str],
            strict: bool = False) -> BuildInfo:
        ...

    def getBuildTarget(
            self,
            info: Union[int, str],
            event: Optional[int] = None,
            strict: bool = False) -> TargetInfo:
        ...

    def getBuildTargets(
            self,
            info: Optional[Union[int, str]] = None,
            event: Optional[int] = None,
            buildTagID: Optional[int] = None,
            destTagID: Optional[int] = None,
            queryOpts: Optional[Dict[str, Any]] = None) -> List[TargetInfo]:
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

    def getChannel(
            self,
            channelInfo: Union[int, str],
            strict: bool = False) -> ChannelInfo:
        ...

    def getFullInheritance(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            reverse: bool = False) -> TagInheritance:
        ...

    def getInheritanceData(
            self,
            tag: Union[int, str],
            event: Optional[int] = None) -> TagInheritance:
        ...

    def getGroupMembers(
            self,
            group: Union[int, str]) -> List[UserInfo]:
        ...

    def getHost(
            self,
            hostInfo: Union[int, str],
            strict: bool = False,
            event: Optional[int] = None) -> HostInfo:
        ...

    def getKojiVersion(self) -> str:
        ...

    def getLastHostUpdate(
            self,
            hostID: int,
            ts: bool = False) -> Union[str, float, None]:
        ...

    def getLatestBuilds(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            Package: Optional[Union[int, str]] = None,
            type: Optional[str] = None) -> List[BuildInfo]:
        ...

    def getLatestMavenArchives(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            inherit: bool = True) -> List[ArchiveInfo]:
        ...

    def getLatestRPMS(
            self,
            tag: Union[int, str],
            package: Optional[Union[int, str]] = None,
            arch: Optional[str] = None,
            event: Optional[int] = None,
            rpmsigs: bool = False,
            type: Optional[str] = None) -> Tuple[List[RPMInfo],
                                                 List[BuildInfo]]:
        ...

    def getPerms(self) -> List[str]:
        ...

    def getRepo(
            self,
            tag: Union[int, str],
            state: Optional[RepoState] = None,
            event: Optional[int] = None,
            dist: bool = False) -> RepoInfo:
        ...

    def getRPM(
            self,
            rpminfo: Union[int, str],
            strict: bool = False,
            multi: bool = False) -> Union[RPMInfo, List[RPMInfo]]:
        ...

    def getUserPerms(
            self,
            userID: Optional[Union[int, str]] = None) -> List[str]:
        ...

    def getTag(
            self,
            taginfo: Union[int, str],
            strict: bool = False,
            event: Optional[int] = None,
            blocked: bool = False) -> TagInfo:
        ...

    def getTagGroups(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            inherit: bool = True,
            incl_pkgs: bool = True,
            incl_reqs: bool = True,
            incl_blocked: bool = False) -> List[TagGroup]:
        ...

    def getTaskInfo(
            self,
            task_id: int,
            request: bool = False,
            strict: bool = False) -> TaskInfo:
        ...

    def getUser(
            self,
            userInfo: Optional[Union[int, str]] = None,
            strict: bool = False,
            krb_brincs: bool = True) -> UserInfo:
        ...

    def getLoggedInUser(self) -> UserInfo:
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
            typeInfo: Optional[dict] = None,
            queryOpts: Optional[Dict] = None,
            imageID: Optional[int] = None,
            archiveID: Optional[int] = None,
            strict: bool = False) -> List[ArchiveInfo]:
        ...

    def listBTypes(
            self,
            query: Optional[Dict[str,str]] = None,
            queryOpts: Optional[dict] = None) -> List[BTypeInfo]:
        ...

    def listCGs(self) -> Dict[str, CGInfo]:
        ...

    def listHosts(
            self,
            arches: Optional[List[str]] = None,
            channelID: Optional[int] = None,
            ready: Optional[bool] = None,
            enabled: Optional[bool] = None,
            userID: Optional[int] = None,
            queryOpts: Optional[dict] = None) -> List[HostInfo]:
        ...

    def listPackages(
            self,
            tagID: Optional[int] = None,
            userID: Optional[int] = None,
            pkgID: Optional[int] = None,
            prefix: Optional[str] = None,
            inherited: bool = False,
            with_dups: bool = False,
            event: Optional[int] = None,
            quertOpts: Optional[dict] = None,
            with_owners: bool = True) -> List[TagPackageInfo]:
        ...

    def listRPMs(
            self,
            buildID: Optional[int] = None,
            buildrootID: Optional[int] = None,
            imageID: Optional[int] = None,
            componentBuildrootID: Optional[int] = None,
            hostID: Optional[int] = None,
            arches: Optional[str] = None,
            queryOpts: Optional[dict] = None) -> List[RPMInfo]:
        ...

    def listTagged(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            inherit: bool = False,
            prefix: Optional[str] = None,
            latest: bool = False,
            package: Optional[Union[int, str]] = None,
            owner: Optional[Union[int, str]] = None,
            type: Optional[str] = None) -> List[BuildInfo]:
        ...

    def listTaggedArchives(
            self,
            tag: Union[int, str],
            event: Optional[int] = None,
            inherit: bool = False,
            latest: bool = False,
            package: Optional[Union[int, str]] = None,
            type: Optional[str] = None) -> Tuple[List[ArchiveInfo],
                                                 List[BuildInfo]]:
        ...

    def listTags(
            self,
            build: Optional[Union[int, str]] = None,
            package: Optional[Union[int, str]] = None,
            perms: bool = True,
            queryOpts: Optional[dict] = None,
            pattern: Optional[str] = None) -> List[TagInfo]:
        ...

    def massTag(
            self,
            tag: Union[int, str],
            builds: List[str]) -> None:
        ...

    def multiCall(
            self,
            strict: bool = False,
            batch: Optional[int] = None) -> List[Union[FaultInfo, List[Any]]]:
        ...

    def packageListAdd(
            self,
            taginfo: Union[int, str],
            pkginfo: str,
            owner: Optional[Union[int, str]] = None,
            block: Optional[bool] = None,
            exta_arches: Optional[str] = None,
            force: bool = False,
            update: bool = False):
        ...

    def queryHistory(
            self,
            tables: Optional[List[str]] = None,
            **kwargs: Any) -> Dict[str, List[Dict[str, Any]]]:
        ...

    def queryRPMSigs(
            self,
            rpm_id: Optional[int] = None,
            sigkey: Optional[str] = None,
            queryOpts: Optional[dict] = None) -> List[RPMSignature]:
        ...

    def repoInfo(
            self,
            repo_id: int,
            struct: bool = False) -> RepoInfo:
        ...

    def search(
            self,
            terms: str,
            type: str,
            matchType: str,
            queryOpts: Optional[dict] = None) -> List[SearchResult]:
        ...

    def setInheritanceData(
            self,
            tag: Union[int, str],
            data: TagInheritance,
            clear: bool = False):
        ...

    def tagBuildBypass(
            self,
            tag: Union[int, str],
            build: Union[int, str],
            force: bool = False,
            notify: bool = False) -> None:
        ...

    def untagBuildBypass(
            self,
            tag: Union[int, str],
            build: Union[int, str],
            strict: bool = True,
            force: bool = False,
            notify: bool = False) -> None:
        ...


def convertFault(fault: Fault) -> GenericError:
    ...


def read_config(
        profile_name: str,
        user_config: Optional[str] = None) -> Dict[str, Any]:
    ...


#
# The end.
