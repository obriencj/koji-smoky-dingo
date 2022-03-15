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
Koji Smoky Dingo - Client utilities for working with the Koji
build system

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from functools import partial
from koji import (
    ClientSession, Fault, GenericError, ParameterError,
    convertFault, read_config)
from koji_cli.lib import activate_session, ensure_connection
from logging import DEBUG, basicConfig
from typing import (
    Any, Callable, Dict, Iterator, Iterable, List,
    Optional, Sequence, TypeVar, Tuple, Union, cast)

from .common import chunkseq
from .types import (
    ArchiveInfo, ArchiveInfos, ArchiveSpec,
    BuildInfo, BuildSpec,
    ChannelInfo, ChannelSpec,
    HostInfo, HostSpec,
    HubVersionSpec,
    PackageInfo, PackageSpec,
    RepoInfo, RepoSpec,
    RPMInfo, RPMInfos, RPMSignature, RPMSpec,
    TagInfo, TagSpec,
    TargetInfo, TargetSpec,
    TaskInfo, TaskSpec,
    UserInfo, UserSpec, )


__all__ = (
    "AnonClientSession",
    "BadDingo",
    "FeatureUnavailable",
    "ManagedClientSession",
    "NoSuchArchive",
    "NoSuchBuild",
    "NoSuchChannel",
    "NoSuchContentGenerator",
    "NoSuchHost",
    "NoSuchPackage",
    "NoSuchPermission",
    "NoSuchRepo",
    "NoSuchRPM",
    "NoSuchTag",
    "NoSuchTarget",
    "NoSuchTask",
    "NoSuchUser",
    "NotPermitted",
    "ProfileClientSession",

    "as_archiveinfo",
    "as_buildinfo",
    "as_channelinfo",
    "as_hostinfo",
    "as_packageinfo",
    "as_repoinfo",
    "as_rpminfo",
    "as_taginfo",
    "as_targetinfo",
    "as_taskinfo",
    "as_userinfo",
    "bulk_load",
    "bulk_load_build_archives",
    "bulk_load_build_rpms",
    "bulk_load_builds",
    "bulk_load_buildroot_archives",
    "bulk_load_buildroot_rpms",
    "bulk_load_buildroots",
    "bulk_load_rpm_sigs",
    "bulk_load_tags",
    "bulk_load_tasks",
    "bulk_load_users",
    "hub_version",
    "iter_bulk_load",
    "version_check",
    "version_require",
)


class ManagedClientSession(ClientSession):
    """
    A `koji.ClientSession` that can be used as via the ``with``
    keyword to provide a managed session that will handle
    authenticated login and logout.

    :since: 1.0
    """

    def __enter__(self):
        self.activate()
        return self


    def __exit__(self, exc_type, _exc_val, _exc_tb):
        self.logout()
        if self.rsession:
            self.rsession.close()
            self.rsession = None
        return (exc_type is None)


    def activate(self):
        """
        Invokes `koji_cli.lib.activate_session` with this session's
        options, which will trigger the appropriate login method.

        :since 2.0:
        """
        return activate_session(self, self.opts)


    @property
    def logger(self):
        # a cached copy of `logging.getLogger('koji')`, assigned
        # during `ClientSession.__init__` invocation.  There are some
        # code paths in the underlying ClientSession which will
        # presume that logging handlers have been configured, without
        # checking that they actually have been. This is likely
        # because the koji command-line interface sets up that logger
        # shortly after parsing initial CLI args. However, when a
        # script uses a ClientSession, that setup won't have
        # happened. Then if the script encounters an error along one
        # of those code paths, an additional logging warning will be
        # output after that path attempts to log at some unconfigured
        # level. This property allows us to set a default
        # configuration if one hasn't been given yet, just before the
        # instance would attempt to use the logger.

        logger = self._logger
        if logger and not logger.handlers:
            basicConfig()

            # the koji CLI will use the --debug and --quiet options to
            # determine the logger level. However, only the debug
            # option is recorded as part of the session options. We'll
            # mimic as much of the logging behavior as we can
            opts = self.opts
            if opts.get('debug') or opts.get('debug_xmlrpc'):
                logger.setLevel(DEBUG)

        return logger


    @logger.setter
    def logger(self, logger):
        self._logger = logger


class ProfileClientSession(ManagedClientSession):
    """
    A `koji.ClientSession` which loads profile config information and
    which can be used via tha ``with`` keyword.

    :since: 1.0
    """

    def __init__(self, profile: str = "koji"):
        """
        :param profile: name of the koji profile to load from local
          configuration locations
        """

        conf = read_config(profile)
        server = conf["server"]
        super().__init__(server, opts=conf)


class AnonClientSession(ProfileClientSession):
    """
    A `koji.ClientSession` which loads profile config information and
    which can be used via the ``with`` keyword.

    Suitable for working with anonymous commands which do not require
    authentication. Does not authenticate, and will only connect
    lazily.

    :since: 1.0
    """

    def __enter__(self):
        # we could always set up a connection ahead of time,
        # but... the connection will be created when we make our first
        # call, so let's be lazy instead.

        # ensure_connection(self)
        return self


    def activate(self):
        """
        Ensures the anonymous session is connected, but does not attempt
        to login.

        :since 2.0:
        """

        ensure_connection(self)


class BadDingo(Exception):
    """
    Generalized base class for exceptions raised from kojismokydingo.
    This class and its subclasses are used to combine a fixed
    complaint string with some specific information. This is a
    convenience primarily for the CLI, but can also be used to track
    more detailed situations where a requested data type wasn't
    present on the koji hub, rather than just working with
    `koji.GenericError`

    :since: 1.0
    """

    complaint: str = "Something bad happened"


    def __str__(self):
        orig = super().__str__()
        return f"{self.complaint}: {orig}"


class NoSuchBuild(BadDingo):
    """
    A build was not found

    :since: 1.0
    """

    complaint = "No such build"


class NoSuchHost(BadDingo):
    """
    A host was not found

    :since: 1.0
    """

    complaint = "No such host"


class NoSuchChannel(BadDingo):
    """
    A channel was not found

    :since: 1.0
    """

    complaint = "No such builder channel"


class NoSuchContentGenerator(BadDingo):
    """
    A content generator was not found

    :since: 1.0
    """

    complaint = "No such content generator"


class NoSuchPackage(BadDingo):
    """
    A package was not found

    :since: 1.1
    """

    complaint = "No such package"


class NoSuchTag(BadDingo):
    """
    A tag was not found

    :since: 1.0
    """

    complaint = "No such tag"


class NoSuchTarget(BadDingo):
    """
    A target was not found

    :since: 1.0
    """

    complaint = "No such target"


class NoSuchTask(BadDingo):
    """
    A task was not found

    :since: 1.0
    """

    complaint = "No such task"


class NoSuchUser(BadDingo):
    """
    A user was not found

    :since: 1.0
    """

    complaint = "No such user"


class NoSuchPermission(BadDingo):
    """
    A permission was not found

    :since: 1.0
    """

    complaint = "No such permission"


class NoSuchArchive(BadDingo):
    """
    An archive was not found

    :since: 1.0
    """

    complaint = "No such archive"


class NoSuchRepo(BadDingo):
    """
    A repository was not found

    :since: 1.1
    """

    complaint = "No such repo"


class NoSuchRPM(BadDingo):
    """
    An RPM was not found
    """

    complaint = "No such RPM"


class NotPermitted(BadDingo):
    """
    A required permission was not associated with the currently logged
    in user account.
    """

    complaint = "Insufficient permissions"


class FeatureUnavailable(BadDingo):
    """
    A given feature isn't available due to the version on the koji hub
    """

    complaint = "The koji hub version doesn't support this feature"


KT = TypeVar('KT')


def iter_bulk_load(
        session: ClientSession,
        loadfn: Callable[[Any], Any],
        keys: Iterable[KT],
        err: bool = True,
        size: int = 100) -> Iterator[Tuple[KT, Any]]:
    """
    Generic bulk loading generator. Invokes the given loadfn on each
    key in keys using chunking multicalls limited to the specified
    size.

    Yields (key, result) pairs in order.

    If err is True (default) then any faults will raise an exception.
    If err is False, then a None will be substituted as the result for
    the failing key.

    :param session: The koji session

    :param loadfn: The loading function, to be invoked in a multicall
      arrangement. Will be called once with each given key from keys

    :param keys: The sequence of keys to be used to invoke loadfn.

    :param err: Whether to raise any underlying fault returns as
      exceptions. Default, True

    :param size: How many calls to loadfn to chunk up for each
      multicall. Default, 100

    :raises koji.GenericError: if err is True and an issue
      occurrs while invoking the loadfn

    :since: 1.0
    """

    for key_chunk in chunkseq(keys, size):
        session.multicall = True

        for key in key_chunk:
            loadfn(key)

        for key, info in zip(key_chunk, session.multiCall(strict=err)):
            if info:
                if "faultCode" in info:
                    if err:
                        raise convertFault(Fault(**info))  # type: ignore
                    else:
                        yield key, None
                else:
                    yield key, info[0]  # type: ignore
            else:
                yield key, None


def bulk_load(
        session: ClientSession,
        loadfn: Callable[[Any], Any],
        keys: Iterable[Any],
        err: bool = True,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[Any, Any]:
    """
    Generic bulk loading function. Invokes the given `loadfn` on each
    key in `keys` using chunking multicalls limited to the specified
    size.

    Returns a dict associating the individual keys with the returned
    value of loadfn. If `results` is specified, it must support
    dict-like assignment via an update method, and will be used in
    place of a newly allocated dict to store and return the results.

    :param session: an active koji client session

    :param loadfn: The loading function, to be invoked in a multicall
      arrangement. Will be called once with each given key from `keys`

    :param keys: The sequence of keys to be used to invoke `loadfn`.
      These keys need to be individually hashable, or the `results`
      value needs to be specified with an instance that accepts
      assignmnet using these values as the key.

    :param err: Whether to raise any underlying fault returns as
      exceptions. Default, `True`

    :param size: How many calls to `loadfn` to chunk up for each
      multicall. Default, `100`

    :param results: storage for `loadfn` results. If specified, must
      support item assignment (like a dict) via an update method, and
      it will be populated and then used as the return value for this
      function. Default, a new dict will be allocated.

    :raises koji.GenericError: if `err` is `True` and an issue
      occurrs while invoking the `loadfn`

    :since: 1.0
    """

    results = {} if results is None else results
    results.update(iter_bulk_load(session, loadfn, keys, err, size))
    return results


def bulk_load_builds(
        session: ClientSession,
        nvrs: Iterable[Union[str, int]],
        err: bool = True,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[Union[int, str],
                                                BuildInfo]:
    """
    Load many buildinfo dicts from a koji client session and a
    sequence of NVRs.

    Returns a dict associating the individual NVRs with their
    resulting buildinfo.

    If err is True (default) then any missing build info will raise a
    `NoSuchBuild` exception. If err is False, then a None will be
    substituted into the ordered dict for the result.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated dict to store and return the
    results.

    :param nvrs: Sequence of build NVRs or build IDs to load

    :param err: Raise an exception if an NVR fails to load. Default,
      True.

    :param size: Count of NVRs to load in a single multicall. Default,
      100

    :param results: mapping to store the results in. Default, produce
      a new dict

    :raises NoSuchBuild: if err is True and any of the given builds
      could not be loaded

    :since: 1.0
    """

    results = {} if results is None else results

    for key, info in iter_bulk_load(session, session.getBuild, nvrs,
                                    False, size):
        if err and not info:
            raise NoSuchBuild(key)
        else:
            results[key] = info

    return results


def bulk_load_tasks(
        session: ClientSession,
        task_ids: Iterable[int],
        request: bool = False,
        err: bool = True,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, TaskInfo]:
    """
    Load many taskinfo dicts from a koji client session and a sequence
    of task IDs.

    Returns a dict associating the individual IDs with their resulting
    taskinfo.

    :param session: an active koji client session

    :param task_ids: IDs of tasks to be loaded

    :param request: if True then load the task's request data as
      well. Default, False

    :param err: raise an exception if a task fails to load. Default,
      True

    :param size: count of tasks to load in a single
      multicall. Default, 100

    :param results: mapping to store the results in. Default, produce
      a new dict

    :raises NoSuchTask: if err is True and a task couldn'tb e loaded

    :since: 1.0
    """

    results = {} if results is None else results

    fn = partial(session.getTaskInfo, request=request)

    for key, info in iter_bulk_load(session, fn, task_ids, False, size):
        if err and not info:
            raise NoSuchTask(key)
        else:
            results[key] = info

    return results


def bulk_load_tags(
        session: ClientSession,
        tags: Iterable[Union[str, int]],
        err: bool = True,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[Union[int, str],
                                                TagInfo]:
    """
    Load many taginfo dicts from tag names or IDs.

    :param session: an active koji client session

    :param tags: tag IDs or names to load

    :param err: Raise an exception if a tag fails to load. Default,
      True.

    :param size: Count of tags to load in a single multicall. Default,
      100

    :param results: mapping to store the results in. Default, produce
      a new dict

    :raises NoSuchTag: if err is True and a tag couldn't be loaded

    :since: 1.0
    """

    results = {} if results is None else results

    if version_check(session, (1, 23)):
        fn = partial(session.getTag, blocked=True)
    else:
        fn = session.getTag  # type: ignore

    for key, info in iter_bulk_load(session, fn, tags, False, size):
        if err and not info:
            raise NoSuchTag(key)
        else:
            results[key] = info

    return results


def bulk_load_rpm_sigs(
        session: ClientSession,
        rpm_ids: Iterable[int],
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, List[RPMSignature]]:
    """
    Set up a chunking multicall to fetch the signatures for a list of
    RPM via `session.queryRPMSigs` for each ID in rpm_ids.

    Returns a dict associating the individual RPM IDs with their
    resulting RPM signature lists.

    If results is non-None, it must support a dict-like update method,
    and will be used in place of a newly allocated dict to store and
    return the results.

    :since: 1.0
    """

    results = {} if results is None else results
    results.update(iter_bulk_load(session, session.queryRPMSigs,
                                  rpm_ids, True, size))
    return results


def bulk_load_buildroot_archives(
        session: ClientSession,
        buildroot_ids: Iterable[int],
        btype: Optional[str] = None,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, List[ArchiveInfo]]:
    """
    Set up a chunking multicall to fetch the archives of buildroots
    via `session.listArchives` for each buildroot ID in buildrood_ids.

    Returns a dict associating the individual buildroot IDs with their
    resulting archive lists.

    If results is non-None, it must support dict-like update method,
    and will be used in place of a newly allocated dict to store and
    return the results.

    :since: 1.0
    """

    results = {} if results is None else results
    fn = lambda i: session.listArchives(componentBuildrootID=i, type=btype)
    results.update(iter_bulk_load(session, fn, buildroot_ids, True, size))
    return results


def bulk_load_buildroot_rpms(
        session: ClientSession,
        buildroot_ids: Iterable[int],
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, List[RPMInfo]]:
    """
    Set up a chunking multicall to fetch the RPMs of buildroots via
    `session.listRPMs` for each buildroot ID in buildrood_ids.

    Returns a dict associating the individual buildroot IDs with their
    resulting RPM lists.

    If results is non-None, it must support dict-like update method,
    and will be used in place of a newly allocated dict to store and
    return the results.

    :since: 1.0
    """

    results = {} if results is None else results
    fn = lambda i: session.listRPMs(componentBuildrootID=i)
    results.update(iter_bulk_load(session, fn, buildroot_ids, True, size))
    return results


def bulk_load_build_archives(
        session: ClientSession,
        build_ids: Iterable[int],
        btype: Optional[str] = None,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, List[ArchiveInfo]]:
    """
    Set up a chunking multicall to fetch the archives of builds
    via `session.listArchives` for each build ID in build_ids.

    Returns a dict associating the individual build IDs with their
    resulting archive lists.

    If results is non-None, it must support dict-like update method,
    and will be used in place of a newly allocated dict to store and
    return the results.

    :since: 1.0
    """

    results = {} if results is None else results
    fn = lambda i: session.listArchives(buildID=i, type=btype)
    results.update(iter_bulk_load(session, fn, build_ids, True, size))
    return results


def bulk_load_build_rpms(
        session: ClientSession,
        build_ids: Iterable[int],
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, List[RPMInfo]]:
    """
    Set up a chunking multicall to fetch the RPMs of builds via
    `session.listRPMS` for each build ID in build_ids.

    Returns a dict associating the individual build IDs with their
    resulting RPM lists.

    If results is non-None, it must support a dict-like update method,
    and will be used in place of a newly allocated dict to store and
    return the results.

    :since: 1.0
    """

    results = {} if results is None else results
    results.update(iter_bulk_load(session, session.listRPMs,
                                  build_ids, True, size))
    return results


def bulk_load_buildroots(
        session: ClientSession,
        broot_ids: Iterable[int],
        size: int = 100,
        results: Optional[dict] = None) -> Dict[int, dict]:
    """
    Set up a chunking multicall to fetch the buildroot data via
    `session.getBuildroot` for each ID in broot_ids.

    Returns a dict associating the individual buildroot IDs with their
    resulting buildroot info dicts.

    If results is non-None, it must support a dict-like update method,
    and will be used in place of a newly allocated dict to store and
    return the results.

    :since: 1.0
    """

    results = {} if results is None else results
    results.update(iter_bulk_load(session, session.getBuildroot,
                                  broot_ids, True, size))
    return results


def bulk_load_users(
        session: ClientSession,
        users: Iterable[Union[int, str]],
        err: bool = True,
        size: int = 100,
        results: Optional[dict] = None) -> Dict[Union[int, str],
                                                UserInfo]:
    """
    Load many userinfo dicts from a koji client session and a sequence of
    user identifiers.

    Returns a dict associating the individual identifiers with their
    resulting userinfo.

    If err is True (default) then any missing user info will raise a
    NoSuchUser exception. If err is False, then a None will be
    substituted into the ordered dict for the result.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated dict to store and return the
    results.

    :param session: active koji session

    :param users: user names or IDs to load

    :param err: halt on problems and raise an exception. Default, True

    :param size: number of users to load in a single
      multicall. Default, 100

    :param results: dict to store results in. Default, allocate a new
      dict

    :raises NoSuchUser: if err is True and a user could not be loaded

    :since: 1.0
    """

    users = tuple(users)
    results = {} if results is None else results

    if not users:
        return results

    # we need to identify which signature the getUser API will
    # support.  Unfortunately the change in signatures happened before
    # there was a way to check the hub version. First we'll check
    # whether there's already a cached answer as to which API is
    # available
    session_vars = vars(session)
    new_get_user = session_vars.get("__new_get_user")

    if new_get_user is None:
        # there wasn't already an answer, so we'll have to find out
        # ourselves. In this case we'll load the first user in the
        # list of users separately, outside of a multicall, and using
        # the as_userinfo function. This function will first try the
        # newer signature. If successful, it will record
        # __new_get_user as True, and we'll know to use the newer
        # signature. If not, the function will retry with the older
        # signature and set __new_get_user to False.

        key = users[0]
        users = users[1:]

        try:
            results[key] = as_userinfo(session, key)
        except NoSuchUser:
            if err:
                raise
            else:
                results[key] = None

        # the use of as_userinfo will have updated the __new_get_user
        # sentinel attribute to either True or False
        new_get_user = session_vars.get("__new_get_user")

    if new_get_user:
        fn = lambda u: session.getUser(u, False, True)
    else:
        fn = session.getUser

    for key, info in iter_bulk_load(session, fn, users, False, size):
        if err and not info:
            raise NoSuchUser(key)
        else:
            results[key] = info

    return results


def as_buildinfo(
        session: ClientSession,
        build: BuildSpec) -> BuildInfo:
    """
    Coerces a build value into a koji build info dict.

    If build is an
     * int, will attempt to load as a build ID
     * str, will attempt to load as an NVR
     * dict, will presume already a build info

    :param session: active koji session

    :param build: value to lookup

    :raises NoSuchBuild: if the build value could not be resolved
      into a build info dict

    :since: 1.0
    """

    if isinstance(build, (str, int)):
        info = session.getBuild(build)
    elif isinstance(build, dict):
        info = build
    else:
        info = None

    if not info:
        raise NoSuchBuild(build)

    return info


def as_channelinfo(
        session: ClientSession,
        channel: ChannelSpec) -> ChannelInfo:
    """
    Coerces a channel value into a koji channel info dict.

    If channel is an
     * int, will attempt to load as a channel ID
     * str, will attempt to load as a channel name
     * dict, will presume already a channel info

    :param session: an active koji client session

    :param channel: value to lookup

    :raises NoSuchChannel: if the channel value could not be resolved
      into a channel info dict

    :since: 1.1
    """

    if isinstance(channel, (str, int)):
        info = session.getChannel(channel)
    elif isinstance(channel, dict):
        info = channel
    else:
        info = None

    if not info:
        raise NoSuchChannel(channel)

    return info


def as_taginfo(
        session: ClientSession,
        tag: TagSpec) -> TagInfo:

    """
    Coerces a tag value into a koji tag info dict.

    If tag is an
     * int, will attempt to load as a tag ID
     * str, will attempt to load as a tag name
     * dict, will presume already a tag info

    :param session: active koji session

    :param tag: value to lookup

    :raises NoSuchTag: if the tag value could not be resolved into a
      tag info dict

    :since: 1.0
    """

    if isinstance(tag, (str, int)):
        if version_check(session, (1, 23)):
            info = session.getTag(tag, blocked=True)
        else:
            info = session.getTag(tag)

    elif isinstance(tag, dict):
        info = tag

    else:
        info = None

    if not info:
        raise NoSuchTag(tag)

    return info


def as_taskinfo(
        session: ClientSession,
        task: TaskSpec) -> TaskInfo:
    """
    Coerces a task value into a koji task info dict.

    If task is an
     * int, will attempt to load as a task ID
     * dict, will presume already a task info

    Note that if this function does attempt to load a task, it will
    request it with the task's request data as well.

    :param session: active koji session

    :param task: value to lookup

    :raises NoSuchTask: if the task value could not be resolved
      into a task info dict

    :since: 1.0
    """

    if isinstance(task, int):
        info = session.getTaskInfo(task, True)
    elif isinstance(task, dict):
        info = task
    else:
        info = None

    if not info:
        raise NoSuchTask(task)

    return info


def as_targetinfo(
        session: ClientSession,
        target: TargetSpec) -> TargetInfo:
    """
    Coerces a target value into a koji target info dict.

    If target is an
     * int, will attempt to load as a target ID
     * str, will attempt to load as a target name
     * dict, will presume already a target info

    :param session: active koji session

    :param target: value to lookup

    :raises NoSuchTarget: if the target value could not be resolved
      into a target info dict

    :since: 1.0
    """

    if isinstance(target, (str, int)):
        info = session.getBuildTarget(target)
    elif isinstance(target, dict):
        info = target
    else:
        info = None

    if not info:
        raise NoSuchTarget(target)

    return info


def as_hostinfo(
        session: ClientSession,
        host: HostSpec) -> HostInfo:
    """
    Coerces a host value into a host info dict.

    If host is an:
     * int, will attempt to load as a host ID
     * str, will attempt to load as a host name
     * dict, will presume already a host info

    :param session: active koji session

    :param host: value to lookup

    :raises NoSuchHost: if the host value could not be resolved
      into a host info dict

    :since: 1.0
    """

    if isinstance(host, (str, int)):
        info = session.getHost(host)
    elif isinstance(host, dict):
        info = host
    else:
        info = None

    if not info:
        raise NoSuchHost(host)

    return info


def as_packageinfo(
        session: ClientSession,
        pkg: PackageSpec) -> PackageInfo:
    """
    Coerces a host value into a host info dict.

    If pkg is an:
     * int, will attempt to load as a package ID
     * str, will attempt to load as a package name
     * dict, will presume already a package info

    :param session: an active koji client session

    :param pkg: value to lookup

    :raises NoSuchPackage: if the pkg value could not be resolved into
      a package info dict

    :since: 1.1
    """

    if isinstance(pkg, (str, int)):
        info = session.getPackage(pkg)
    elif isinstance(pkg, dict):
        info = pkg
    else:
        info = None

    if not info:
        raise NoSuchPackage(pkg)

    return info


def as_archiveinfo(
        session: ClientSession,
        archive: ArchiveSpec) -> ArchiveInfo:
    """
    Coerces an archive value into an archive info dict.

    If archive is an:
     * int, will attempt to load as an archive ID
     * str, will attempt to load as the first-found archive matching
       the given filename
     * dict, will presume already an archive info

    :param session: active koji session

    :param archive: value to lookup

    :raises NoSuchArchive: if the archive value could not be resolved
      into an archive info dict

    :since: 1.0
    """

    if isinstance(archive, int):
        info = session.getArchive(archive)

    elif isinstance(archive, str):
        found = session.listArchives(filename=archive)
        info = found[0] if found else None

    elif isinstance(archive, dict):
        info = archive

    else:
        info = None

    if not info:
        raise NoSuchArchive(archive)

    return info


def as_repoinfo(
        session: ClientSession,
        repo: RepoSpec) -> RepoInfo:
    """
    Coerces a repo value into a Repo info dict.

    If repo is an:
     * dict with name, will attempt to load the current repo from a
       tag by that name
     * str, will attempt to load the current repo from a tag by name
     * int, will attempt to load the repo by ID
     * dict, will presume already a repo info

    :param session: active koji session

    :param repo: value to lookup

    :raises NoSuchRepo: if the repo value could not be resolved
      into a repo info dict

    :since: 1.1
    """

    info: RepoInfo = None

    if isinstance(repo, dict):
        if "name" in repo:
            tag = cast(TagInfo, repo)
            repo = tag["name"]
        else:
            info = cast(RepoInfo, repo)

    if isinstance(repo, str):
        repotag = session.getRepo(repo)
        if repotag is None:
            raise NoSuchRepo(repo)
        repo = repotag["id"]

    if isinstance(repo, int):
        info = session.repoInfo(repo)

    if not info:
        raise NoSuchRepo(repo)

    return info


def as_rpminfo(
        session: ClientSession,
        rpm: RPMSpec) -> RPMInfo:
    """
    Coerces a host value into a RPM info dict.

    If rpm is specified as an:
     * int, will attempt to load as a RPM ID
     * str, will attempt to load as a RPM NVRA
     * dict, will presume already an RPM info

    :param session: active koji session

    :param rpm: value to lookup

    :raises NoSuchRPM: if the rpm value could not be resolved
      into a RPM info dict

    :since: 1.0
    """

    info: RPMInfo

    if isinstance(rpm, (str, int)):
        info = session.getRPM(rpm)  # type: ignore
    elif isinstance(rpm, dict):
        info = rpm
    else:
        info = None

    if not info:
        raise NoSuchRPM(rpm)

    return info


def as_userinfo(
        session: ClientSession,
        user: UserSpec) -> UserInfo:
    """
    Resolves user to a userinfo dict.

    If user is a str or int, then getUser will be invoked. If user is
    already a dict, it's presumed to be a userinfo already and it's
    returned unaltered.

    :param session: active koji session

    :param user: Name, ID, or User Info describing a koji user

    :raises NoSuchUser: when user cannot be found

    :since: 1.0
    """

    if isinstance(user, (str, int)):
        session_vars = vars(session)
        new_get_user = session_vars.get("__new_get_user")

        if new_get_user:
            # we've tried the new way and it worked, so keep doing it.
            info = session.getUser(user, False, True)

        elif new_get_user is None:
            # an API incompatibility emerged at some point in Koji's
            # past, so we need to try the new way first and fall back
            # to the older signature if that fails. This happened
            # before Koji hub started reporting its version, so we
            # cannot use the version_check function to gate this.
            try:
                info = session.getUser(user, False, True)
                session_vars["__new_get_user"] = True

            except ParameterError:
                info = session.getUser(user)
                session_vars["__new_get_user"] = False

        else:
            # we've already tried the new way once and it didn't work.
            info = session.getUser(user)

    elif isinstance(user, dict):
        info = user

    else:
        info = None

    if not info:
        raise NoSuchUser(user)

    return info


def _int(val):
    if isinstance(val, str) and val.isdigit():
        val = int(val)
    return val


def hub_version(
        session: ClientSession) -> Tuple[int]:
    """
    Wrapper for ``session.getKojiVersion`` which caches the results on
    the session and splits the value into a tuple of ints for easy
    comparison.

    If the getKojiVersion method isn't implemented on the hub, we
    presume that we're version 1.22 ``(1, 22)`` which is the last
    version before the getKojiVersion API was added.

    :param session: active koji session

    :since: 1.0
    """

    # we need to use this instead of getattr as koji sessions will
    # automatically create all missing properties as proxies to a
    # remote hub method.
    session_vars = vars(session)

    hub_ver = session_vars.get("__hub_version", None)
    if hub_ver is None:
        try:
            hub_ver = session.getKojiVersion()
        except GenericError:
            pass

        if hub_ver is None:
            hub_ver = (1, 22)

        elif isinstance(hub_ver, str):
            hub_ver = tuple(map(_int, hub_ver.split(".")))

        session_vars["__hub_version"] = hub_ver

    return hub_ver


def version_check(
        session: ClientSession,
        minimum: HubVersionSpec = (1, 23)) -> bool:
    """
    Verifies that the requested minimum version is met compared
    against session.getKojiVersion.

    If the getKojiVersion method isn't implemented on the hub, we
    presume that we're version 1.22 (the last version before
    getKojiVersion was added). Because of this, checking for minimum
    versions lower than 1.23 will always return True.

    Version is specified as a tuple of integers, eg. 1.23 is ``(1,
    23)``

    :param session: active koji session

    :param minimum: Minimum version required. Default, ``(1, 23)``

    :since: 1.0
    """

    if isinstance(minimum, str):
        minimum = tuple(map(_int, minimum.split(".")))

    hub_ver = hub_version(session)

    return bool(hub_ver and hub_ver >= minimum)


def version_require(
        session: ClientSession,
        minimum: HubVersionSpec = (1, 23),
        message: Optional[str] = None) -> bool:
    """
    Verifies that the requested minimum version is met compared
    against ``session.getKojiVersion()``

    If the getKojiVersion method isn't implemented on the hub, we
    presume that we're version 1.22 (the last version before
    getKojiVersion was added). Because of this, checking for minimum
    versions lower than 1.23 will always return True.

    Version is specified as a tuple of integers, eg. 1.23 is ``(1,
    23)``

    If the version requirement is not met, a `FeatureUnavailable`
    exception is raised, with the given message. If message is not
    provided, a simple one is constructed based on the minimum value.

    :param session: active koji session

    :param minimum: Minimum version required. Default, ``(1, 23)``

    :param message: Message to use in exception if version check
      fails. Default, with a minimum of ``(1, 23)``, ``"requires >=
      1.23"``

    :raises FeatureUnavailable: If the minimum version is not met

    :since: 1.0
    """

    if version_check(session, minimum=minimum):
        return True

    if message is None:
        if isinstance(minimum, (list, tuple)):
            minimum = ".".join(str(m) for m in minimum)
        message = f"requires >= {minimum}"

    raise FeatureUnavailable(message)


#
# The end.
