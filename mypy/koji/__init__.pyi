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


from __future__ import annotations


from configparser import ConfigParser, RawConfigParser
from datetime import datetime
from typing import (
    Any, Dict, Generic, Iterable, List, Optional, Tuple,
    TypedDict, TypeVar, Union, Set, overload, )
from xmlrpc.client import DateTime

from kojismokydingo.types import (
    ArchiveInfo, ArchiveTypeInfo, BuildInfo, BuildrootInfo, BuildState,
    BTypeInfo, ChannelInfo, CGInfo, HostInfo, ListTasksOptions,
    PackageInfo, PermInfo, QueryOptions, RepoInfo, RepoState, RPMInfo,
    RPMSignature, SearchResult, TagBuildInfo, TagInfo, TagGroupInfo,
    TagInheritance, TagPackageInfo, TargetInfo, TaskInfo,
    UserGroup, UserInfo, )

# local mypy plugin and special decorator
from proxytype import proxytype

from contextlib import AbstractContextManager
from typing_extensions import Self


# Koji 1.34.0 intentionally broke API compatibility and removed these.
# https://pagure.io/koji/pull-request/3818

# AUTHTYPE_NORMAL: int
# AUTHTYPE_KERB: int
# AUTHTYPE_SSL: int
# AUTHTYPE_GSSAPI: int

BASEDIR: str

PRIO_DEFAULT: int

# REPO_DELETED: int
# REPO_EXPIRED: int
# REPO_INIT: int
# REPO_PROBLEM: int
# REPO_READY: int

REPO_MERGE_MODES: Set[str]

RPM_SIGTAG_GPG: int
RPM_SIGTAG_MD5: int
RPM_SIGTAG_PGP: int
RPM_SIGTAG_RSA: int

RPM_TAG_FILEDIGESTALGO: int
RPM_TAG_HEADERSIGNATURES: int

AUTHTYPES: "Enum"
BR_STATES: "Enum"
BR_TYPES: "Enum"
BUILD_STATES: "Enum"
CHECKSUM_TYPES: "Enum"
REPO_STATES: "Enum"
TAG_UPDATE_TYPES: "Enum"
TASK_STATES: "Enum"
USERTYPES: "Enum"
USER_STATUS: "Enum"

pathinfo: "PathInfo"


# === Exceptions ===

class GenericError(Exception):
    faultCode: int
    fromFault: bool


class ActionNotAllowed(GenericError):
    ...


class ApplianceError(GenericError):
    ...


class AuthError(GenericError):
    ...


class AuthExpired(AuthError):
    ...


class AuthLockError(AuthError):
    ...


class BuildError(GenericError):
    ...


class BuildrootError(BuildError):
    ...


class ConfigurationError(GenericError):
    ...


class LiveCDError(GenericError):
    ...


class LiveMediaError(GenericError):
    ...


class LockError(GenericError):
    ...


class ParameterError(GenericError):
    ...


class RetryError(AuthError):
    ...


class TagError(GenericError):
    ...


# === Classes ===

class ClientSession:

    baseurl: str
    multicall: "MultiCallHack"
    opts: Dict[str, Any]

    @property
    def hub_version(self) -> Tuple[int, ...]:
        """
        :since: koji 1.35
        """
        ...

    @property
    def hub_version_str(self) -> str:
        """
        :since: koji 1.35
        """
        ...

    def __init__(
            self,
            baseurl: str,
            opts: Optional[Dict[str, Any]] = None,
            sinfo: Optional[Dict[str, Any]] = None):
        ...

    def count(
            self,
            methodName: str,
            *args: Any,
            **kw: Any) -> int:
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
        ...

    def disableUser(
            self,
            username: Union[int, str]) -> None:
        ...

    def editTag2(
            self,
            taginfo: Union[int, str],
            **kwargs) -> None:
        ...

    def enableUser(
            self,
            username: Union[int, str]) -> None:
        ...

    def exclusiveSession(self, *args, **kwargs) -> None:
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
            queryOpts: Optional[QueryOptions] = None) -> List[TargetInfo]:
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

    def getGroupMembers(
            self,
            group: Union[int, str]) -> List[UserInfo]:
        ...

    def getUserGroups(
            self,
            user: Union[int, str]) -> List[UserGroup]:
        """
        :since: koji 1.35
        """
        ...

    def getHost(
            self,
            hostInfo: Union[int, str],
            strict: bool = False,
            event: Optional[int] = None) -> HostInfo:
        ...

    def getInheritanceData(
            self,
            tag: Union[int, str],
            event: Optional[int] = None) -> TagInheritance:
        ...

    def getKojiVersion(self) -> str:
        """
        :since: koji 1.23
        """
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
            package: Optional[Union[int, str]] = None,
            type: Optional[str] = None) -> List[TagBuildInfo]:
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

    def getLoggedInUser(self) -> UserInfo:
        ...

    def getPackage(
            self,
            info: Union[int, str],
            strict: bool = False,
            create: bool = False) -> PackageInfo:
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

    @overload
    def getRPMHeaders(
            self,
            rpmID: Optional[int] = None,
            taskID: Optional[int] = None,
            filepath: Optional[str] = None,
            headers: Optional[List[str]] = None) -> Dict[str, Any]:
        ...

    @overload
    def getRPMHeaders(
            self,
            rpmID: Optional[int] = None,
            taskID: Optional[int] = None,
            filepath: Optional[str] = None,
            headers: Optional[List[str]] = None,
            strict: Optional[bool] = False) -> Dict[str, Any]:
        """
        :since: koji 1.29.0
        """
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
            incl_blocked: bool = False) -> List[TagGroupInfo]:
        ...

    def getTaskChildren(
            self,
            task_id: int,
            request: Optional[bool] = False,
            strict: Optional[bool] = False) -> List[TaskInfo]:
        ...

    @overload
    def getTaskInfo(
            self,
            task_id: int,
            request: bool = False,
            strict: bool = False) -> TaskInfo:
        ...

    @overload
    def getTaskInfo(
            self,
            task_id: List[int],
            request: bool = False,
            strict: bool = False) -> List[TaskInfo]:
        ...

    @overload
    def getUser(
            self,
            userInfo: Optional[Union[int, str]] = None,
            strict: bool = False,
            krb_princs: bool = True) -> UserInfo:
        ...

    @overload
    def getUser(
            self,
            userInfo: Optional[Union[int, str]] = None,
            strict: bool = False,
            krb_princs: bool = True,
            groups: bool = False) -> UserInfo:
        """
        :since: koji 1.34
        """
        ...

    @overload
    def getUserPerms(
            self,
            userID: Optional[Union[int, str]] = None) -> List[str]:
        ...

    @overload
    def getUserPerms(
            self,
            userID: Optional[Union[int, str]] = None,
            with_groups: bool = True) -> List[str]:
        """
        :since: koji 1.34
        """
        ...

    def getUserPermsInheritance(
            self,
            userID: Union[int, str]) -> Dict[str, List[str]]:
        """
        :since: koji 1.34
        """
        ...

    def gssapi_login(
            self,
            principal: Optional[str] = None,
            keytab: Optional[str] = None,
            ccache: Optional[str] = None,
            proxyuser: Optional[str] = None) -> bool:
        ...

    def hasPerm(
            self,
            perm: str,
            strict: bool = False) -> bool:
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
            queryOpts: Optional[QueryOptions] = None,
            imageID: Optional[int] = None,
            archiveID: Optional[int] = None,
            strict: bool = False) -> List[ArchiveInfo]:
        ...

    def listBTypes(
            self,
            query: Optional[Dict[str, str]] = None,
            queryOpts: Optional[QueryOptions] = None) -> List[BTypeInfo]:
        ...

    def listBuilds(
            self,
            packageID: Optional[int] = None,
            userID: Optional[int] = None,
            taskID: Optional[int] = None,
            prefix: Optional[str] = None,
            state: Optional[BuildState] = None,
            volumeID: Optional[int] = None,
            source: Optional[str] = None,
            createdBefore: Optional[str] = None,
            createdAfter: Optional[str] = None,
            completeBefore: Optional[str] = None,
            completeAfter: Optional[str] = None,
            type: Optional[str] = None,
            typeInfo: Optional[Dict] = None,
            queryOpts: Optional[QueryOptions] = None,
            pattern: Optional[str] = None,
            cgID: Optional[int] = None,
            draft: Optional[bool] = None) -> List[BuildInfo]:
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
            queryOpts: Optional[QueryOptions] = None) -> List[HostInfo]:
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
            queryOpts: Optional[dict] = None,
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
            queryOpts: Optional[QueryOptions] = None) -> List[RPMInfo]:
        ...

    @overload
    def listUsers(
            self,
            userType: int = 0,
            prefix: Optional[str] = None,
            queryOpts: Optional[QueryOptions] = None) -> List[UserInfo]:
        ...

    @overload
    def listUsers(
            self,
            userType: int = 0,
            prefix: Optional[str] = None,
            queryOpts: Optional[QueryOptions] = None,
            perm: Optional[str] = None,
            inherited_perm: bool = False) -> List[UserInfo]:
        """
        :since: koji 1.35
        """
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
            type: Optional[str] = None) -> List[TagBuildInfo]:
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
            queryOpts: Optional[QueryOptions] = None,
            pattern: Optional[str] = None) -> List[TagInfo]:
        ...

    def listTasks(
            self,
            opts: Optional[ListTasksOptions] = None,
            queryOpts: Optional[QueryOptions] = None) -> List[TaskInfo]:
        ...

    def login(
            self,
            opts: Optional[Dict[str, Any]] = None) -> bool:
        ...

    def logout(self) -> None:
        ...

    def massTag(
            self,
            tag: Union[int, str],
            builds: List[Union[int, str]]) -> None:
        """
        :since: koji 1.30
        """
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
            queryOpts: Optional[QueryOptions] = None) -> List[RPMSignature]:
        ...

    def repoInfo(
            self,
            repo_id: int,
            struct: bool = False) -> RepoInfo:
        ...

    def resubmitTask(
            self,
            taskID: int) -> int:
        ...

    def search(
            self,
            terms: str,
            type: str,
            matchType: str,
            queryOpts: Optional[QueryOptions] = None) -> List[SearchResult]:
        ...

    def setInheritanceData(
            self,
            tag: Union[int, str],
            data: TagInheritance,
            clear: bool = False) -> None:
        ...

    def ssl_login(
            self,
            cert: Optional[str] = None,
            ca: Optional[str] = None,
            serverca: Optional[str] = None,
            proxyuser: Optional[str] = None) -> bool:
        ...

    def tagBuildBypass(
            self,
            tag: Union[int, str],
            build: Union[int, str],
            force: bool = False,
            notify: bool = False) -> None:
        ...

    def tagChangedSinceEvent(
            self,
            event: int,
            taglist: List[int]) -> bool:
        ...

    def untagBuildBypass(
            self,
            tag: Union[int, str],
            build: Union[int, str],
            strict: bool = True,
            force: bool = False,
            notify: bool = False) -> None:
        ...


class Enum(dict):
    def __init__(
            self,
            args: Iterable[str]):
        ...

    @overload
    def get(self,
            key: int,
            default: Any = None) -> Optional[str]:
        ...

    @overload
    def get(self,
            key: str,
            default: Any = None) -> Optional[int]:
        ...

    def getnum(self,
               key: Union[str, int]) -> int:
        ...


class Fault:
    def __init__(
            self,
            faultCode: int,
            faultString: str,
            **extra: Dict[str,Any]):
        ...


class FaultInfo(TypedDict):
    faultCode: int
    faultString: str


class PathInfo:
    topdir: str

    def __init__(
            self,
            topdir: Optional[str] = None):
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
            volume: Optional[str] = None) -> str:
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

    def repo(
            self,
            repo_id: int,
            tag_str: str) -> str:
        ...

    def rpm(
            self,
            rpminfo: RPMInfo) -> str:
        ...

    def sighdr(
            self,
            rinfo: RPMInfo,
            sigkey: str) -> str:
        ...

    def signed(
            self,
            rpminfo: RPMInfo,
            sigkey: str) -> str:
        ...

    def taskrelpath(
            self,
            task_id: int) -> str:
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

    def work(
            self,
            volume=Optional[str]) -> str:
        ...


class RawHeader:
    def __init__(self, data: bytes):
        ...

    def get(self,
            key: int,
            default: Any = None,
            decode: Optional[bool] = None,
            single: bool = False) -> Any:
        ...


# === Functions ===

def _fix_print(
        value: Union[str, bytes]) -> str:
    ...


def _open_text_file(
        path: str,
        mode: str = 'rt'):
    ...


def add_file_logger(
        logger: str,
        fn: str) -> None:
    ...


def add_mail_logger(
        logger: str,
        addr: str) -> None:
    ...


def add_stderr_logger(
        logger: str) -> None:
    ...


def buildLabel(
        buildInfo: BuildInfo,
        showEpoch: bool = False) -> str:
    ...


def canonArch(
        arch: str) -> str:
    ...


def check_NVR(
        nvr: Union[str, Dict[str, Union[str, int]]],
        strict: bool = False) -> bool:
    ...


def convertFault(fault: Fault) -> GenericError:
    ...


def daemonize() -> None:
    ...


def dump_json(
        filepath: str,
        data: Any,
        indent: int = 4,
        sort_keys: bool = False) -> None:
    ...


def ensuredir(
        directory: str) -> None:
    ...


def fixEncoding(
        value: Any,
        fallback: str = 'iso8859-15',
        remove_nonprintable: bool = False) -> str:
    ...


def fix_encoding(
        value: str,
        fallback: str = 'iso8859-15',
        remove_nonprintable: bool = False) -> str:
    ...


def formatTime(
        value: Union[int, float, datetime, DateTime]) -> str:
    ...


def genMockConfig(
        name: str,
        arch: str,
        managed: bool = True,
        repoid: Optional[int] = None,
        tag_name: Optional[str] = None,
        **opts) -> str:
    ...


def get_header_field(
        hdr: bytes,
        name: str,
        src_arch: bool = False) -> Union[str, List[str]]:
    ...


def get_header_fields(
        X: Union[bytes, str],
        fields: Optional[List[str]],
        src_arch: bool = False) -> Dict[str, Union[str, List[str]]]:
    ...


def get_rpm_header(
        f: Union[bytes, str],
        ts: Optional[int] = None) -> bytes:
    ...


def get_rpm_headers(
        f: Any,
        ts: Optional[int] = None) -> bytes:
    ...


def get_sigpacket_key_id(
        sigpacket: str) -> str:
    ...


def grab_session_options(
        options: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    ...


def hex_string(s: str) -> str:
    ...


def is_debuginfo(
        name: str) -> bool:
    ...


def load_json(filepath: str) -> Any:
    ...


def maven_info_to_nvr(
        maveninfo: Dict[str, Any]) -> Dict[str, Any]:
    ...


def openRemoteFile(
        relpath: str,
        topurl: Optional[str],
        topdir: Optional[str],
        tempdir: Optional[str]):
    ...


def parse_NVR(nvr: str) -> Dict[str, Union[str, int]]:
    ...


def parse_NVRA(nvra: str) -> Dict[str, Union[str, int]]:
    ...


def parse_arches(
        arches: str,
        to_list: bool = False,
        strict: bool = False,
        allow_none: bool = False) -> Union[str, List[str]]:
    ...


def read_config(
        profile_name: str,
        user_config: Optional[str] = None) -> Dict[str, Any]:
    ...


def read_config_files(
        config_files: List[Union[str, Tuple[str, bool]]],
        raw: bool = False) -> Union[RawConfigParser, ConfigParser]:
    ...


# === MultiCallSession ===


VirtualResultType = TypeVar("VirtualResultType")


class VirtualCall(Generic[VirtualResultType]):
    result: VirtualResultType


@proxytype(ClientSession, VirtualCall)
class MultiCallSession:
    """
    All of the same methods from a `ClientSession`, but wrapped to
    return `VirtualCall` instances instead.
    """

    # KSD doesn't use this type directly and I didn't want the proxytype
    # plugin to become a runtime dependency of KSD itself, so I left its
    # definition here rather than in `kojismokydingo.types` where it will
    # only be utilized when running mypy.
    ...


class MultiCallHack:

    def __set__(self, obj: Any, value: bool) -> None:
        # assignment to bool, eg. `session.multicall = True`
        ...

    def __bool__(self) -> bool:
        ...

    def __nonzero__(self) -> bool:
        ...

    def __call__(
            self,
            strict: Optional[bool] = False,
            batch: Optional[int] = None) -> \
            AbstractContextManager[MultiCallSession]:
        ...


# The end.
