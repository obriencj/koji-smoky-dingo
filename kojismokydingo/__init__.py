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


from collections import OrderedDict
from functools import partial
from koji import (
    ClientSession, Fault, GenericError, ParameterError,
    convertFault, read_config)
from koji_cli.lib import activate_session, ensure_connection
from six.moves import map, zip

from .common import chunkseq


__all__ = (
    "AnonClientSession",
    "BadDingo",
    "FeatureUnavailable",
    "ManagedClientSession",
    "NoSuchArchive",
    "NoSuchBuild",
    "NoSuchChannel",
    "NoSuchContentGenerator",
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
        activate_session(self, self.opts)
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        self.logout()
        if self.rsession:
            self.rsession.close()
            self.rsession = None
        return (exc_type is None)


class ProfileClientSession(ManagedClientSession):
    """
    A `koji.ClientSession` which loads profile config information and
    which can be used via tha ``with`` keyword.

    :since: 1.0
    """

    def __init__(self, profile="koji"):
        conf = read_config(profile)
        server = conf["server"]
        super(ProfileClientSession, self).__init__(server, opts=conf)


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

    complaint = "Something bad happened"

    def __str__(self):
        orig = super(BadDingo, self).__str__()
        return ": ".join([self.complaint, orig])


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

    :since: 1.0
    """

    complaint = "No such RPM"


class NotPermitted(BadDingo):
    """
    A required permission was not associated with the currently logged
    in user account.

    :since: 1.0
    """

    complaint = "Insufficient permissions"


class FeatureUnavailable(BadDingo):
    """
    A given feature isn't available due to the version on the koji hub
    """

    complaint = "The koji hub version doesn't support this feature"


def iter_bulk_load(session, loadfn, keys, err=True, size=100):
    """
    Generic bulk loading generator. Invokes the given loadfn on each
    key in keys using chunking multicalls limited to the specified
    size.

    Yields (key, result) pairs in order.

    If err is True (default) then any faults will raise an exception.
    If err is False, then a None will be substituted as the result for
    the failing key.

    :param session: The koji session

    :type session: `koji.ClientSession`

    :param loadfn: The loading function, to be invoked in a multicall
      arrangement. Will be called once with each given key from keys

    :type loadfn: Callable[[object], object]

    :param keys: The sequence of keys to be used to invoke loadfn.

    :type keys: list[object]

    :param err: Whether to raise any underlying fault returns as
      exceptions. Default, True

    :type err: bool, optional

    :param size: How many calls to loadfn to chunk up for each
      multicall. Default, 100

    :type size: int, optional

    :raises koji.GenericError: if err is True and an issue
      occurrs while invoking the loadfn

    :rtype: Generator[tuple[object, object]]
    """

    for key_chunk in chunkseq(keys, size):
        session.multicall = True

        for key in key_chunk:
            loadfn(key)

        for key, info in zip(key_chunk, session.multiCall(strict=err)):
            if info:
                if "faultCode" in info:
                    if err:
                        raise convertFault(Fault(**info))
                    else:
                        yield key, None
                else:
                    yield key, info[0]
            else:
                yield key, None


def bulk_load(session, loadfn, keys, err=True, size=100, results=None):
    """
    Generic bulk loading function. Invokes the given `loadfn` on each
    key in `keys` using chunking multicalls limited to the specified
    size.

    Returns an `OrderedDict` associating the individual keys with the
    returned value of loadfn. If `results` is specified, it must
    support dict-like assignment via an update method, and will be
    used in place of a newly allocated `OrderedDict` to store and
    return the results.

    :param session: The koji session

    :type session: `koji.ClientSession`

    :param loadfn: The loading function, to be invoked in a multicall
      arrangement. Will be called once with each given key from `keys`

    :type loadfn: Callable[[object], object]

    :param keys: The sequence of keys to be used to invoke `loadfn`.
      These keys need to be individually hashable, or the `results`
      value needs to be specified with an instance that accepts
      assignmnet using these values as the key.

    :type keys: list[object]

    :param err: Whether to raise any underlying fault returns as
      exceptions. Default, True

    :type err: bool, optional

    :param size: How many calls to `loadfn` to chunk up for each
      multicall. Default, 100

    :type size: int, optional

    :param results: storage for `loadfn` results. If specified, must
      support item assignment (like a dict) via an update method, and
      it will be populated and then used as the return value for this
      function. Default, a new `OrderedDict` will be allocated.

    :type results: dict, optional

    :raises koji.GenericError: if `err` is `True` and an issue
      occurrs while invoking the `loadfn`

    :rtype: dict[object, object]
    """

    results = OrderedDict() if results is None else results
    results.update(iter_bulk_load(session, loadfn, keys, err, size))
    return results


def bulk_load_builds(session, nvrs, err=True, size=100, results=None):
    """
    Load many buildinfo dicts from a koji client session and a
    sequence of NVRs.

    Returns an OrderedDict associating the individual NVRs with their
    resulting buildinfo.

    If err is True (default) then any missing build info will raise a
    NoSuchBuild exception. If err is False, then a None will be
    substituted into the ordered dict for the result.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated OrderedDict to store and
    return the results.

    :param nvrs: Sequence of build NVRs or build IDs to load

    :type nvrs: Iterator[str] or Iterator[int]

    :param err: Raise an exception if an NVR fails to load. Default,
      True.

    :type err: bool, optional

    :param size: Count of NVRs to load in a single multicall. Default,
      100

    :type size: int, optional

    :param results: mapping to store the results in. Default, produce
      a new OrderedDict

    :type results: Mapping, optional

    :rtype: Mapping
    """

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, session.getBuild, nvrs,
                                    False, size):
        if err and not info:
            raise NoSuchBuild(key)
        else:
            results[key] = info

    return results


def bulk_load_tasks(session, task_ids, request=False,
                    err=True, size=100, results=None):
    """
    Load many taskinfo dicts from a koji client session and a sequence
    of task IDs.

    Returns an OrderedDict associating the individual IDs with their
    resulting taskinfo.
    """

    results = OrderedDict() if results is None else results

    fn = partial(session.getTaskInfo, request=request)

    for key, info in iter_bulk_load(session, fn, task_ids, False, size):
        if err and not info:
            raise NoSuchTask(key)
        else:
            results[key] = info

    return results


def bulk_load_tags(session, tags, err=True, size=100, results=None):
    """
    :param err: Raise an exception if a tag fails to load. Default,
      True.

    :type err: bool, optional

    :param size: Count of tags to load in a single multicall. Default,
      100

    :type size: int, optional
    """

    results = OrderedDict() if results is None else results

    if version_check(session, (1, 23)):
        fn = partial(session.getTag, blocked=True)
    else:
        fn = session.getTag

    for key, info in iter_bulk_load(session, fn, tags, False, size):
        if err and not info:
            raise NoSuchTag(key)
        else:
            results[key] = info

    return results


def bulk_load_rpm_sigs(session, rpm_ids, size=100, results=None):
    """
    Set up a chunking multicall to fetch the signatures for a list of
    RPM via `session.queryRPMSigs` for each ID in rpm_ids.

    Returns an OrderedDict associating the individual RPM IDs with their
    resulting RPM signature lists.

    If results is non-None, it must support a dict-like update method,
    and will be used in place of a newly allocated OrderedDict to
    store and return the results.
    """

    results = OrderedDict() if results is None else results
    results.update(iter_bulk_load(session, session.queryRPMSigs,
                                  rpm_ids, True, size))
    return results


def bulk_load_buildroot_archives(session, buildroot_ids, btype=None,
                                 size=100, results=None):
    """
    Set up a chunking multicall to fetch the archives of buildroots
    via `session.listArchives` for each buildroot ID in buildrood_ids.

    Returns an OrderedDict associating the individual buildroot IDs with
    their resulting archive lists.

    If results is non-None, it must support dict-like update method,
    and will be used in place of a newly allocated OrderedDict to
    store and return the results.
    """

    results = OrderedDict() if results is None else results
    fn = lambda i: session.listArchives(componentBuildrootID=i, type=btype)
    results.update(iter_bulk_load(session, fn, buildroot_ids, True, size))
    return results


def bulk_load_buildroot_rpms(session, buildroot_ids,
                             size=100, results=None):
    """
    Set up a chunking multicall to fetch the RPMs of buildroots via
    `session.listRPMs` for each buildroot ID in buildrood_ids.

    Returns an OrderedDict associating the individual buildroot IDs with
    their resulting RPM lists.

    If results is non-None, it must support dict-like update method,
    and will be used in place of a newly allocated OrderedDict to
    store and return the results.
    """

    results = OrderedDict() if results is None else results
    fn = lambda i: session.listRPMs(componentBuildrootID=i)
    results.update(iter_bulk_load(session, fn, buildroot_ids, True, size))
    return results


def bulk_load_build_archives(session, build_ids, btype=None,
                             size=100, results=None):
    """
    Set up a chunking multicall to fetch the archives of builds
    via `session.listArchives` for each build ID in build_ids.

    Returns an OrderedDict associating the individual build IDs with
    their resulting archive lists.

    If results is non-None, it must support dict-like update method,
    and will be used in place of a newly allocated OrderedDict to
    store and return the results.
    """

    results = OrderedDict() if results is None else results
    fn = lambda i: session.listArchives(buildID=i, type=btype)
    results.update(iter_bulk_load(session, fn, build_ids, True, size))
    return results


def bulk_load_build_rpms(session, build_ids, size=100, results=None):
    """
    Set up a chunking multicall to fetch the RPMs of builds via
    `session.listRPMS` for each build ID in build_ids.

    Returns an OrderedDict associating the individual build IDs with
    their resulting RPM lists.

    If results is non-None, it must support a dict-like update method,
    and will be used in place of a newly allocated OrderedDict to
    store and return the results.
    """

    results = OrderedDict() if results is None else results
    results.update(iter_bulk_load(session, session.listRPMs,
                                  build_ids, True, size))
    return results


def bulk_load_buildroots(session, broot_ids, size=100, results=None):
    """
    Set up a chunking multicall to fetch the buildroot data via
    `session.getBuildroot` for each ID in broot_ids.

    Returns an OrderedDict associating the individual buildroot IDs
    with their resulting buildroot info dicts.

    If results is non-None, it must support a dict-like update method,
    and will be used in place of a newly allocated OrderedDict to
    store and return the results.
    """

    results = OrderedDict() if results is None else results
    results.update(iter_bulk_load(session, session.getBuildroot,
                                  broot_ids, True, size))
    return results


def bulk_load_users(session, users, err=True, size=100, results=None):
    """
    Load many userinfo dicts from a koji client session and a sequence of
    user identifiers.

    Returns an OrderedDict associating the individual identifiers with
    their resulting userinfo.

    If err is True (default) then any missing user info will raise a
    NoSuchUser exception. If err is False, then a None will be
    substituted into the ordered dict for the result.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated OrderedDict to store and
    return the results.

    :param session: active koji session

    :type session: koji.ClientSession

    :param users: user names or IDs to load

    :type users: Iterator[str] or Iterator[int]

    :param err: halt on problems and raise an exception. Default, True

    :type err: bool, optional

    :param size: number of users to load in a single
      multicall. Default, 100

    :type size: int, optional

    :param results: dict to store results in. Default, allocate a new
      OrderedDict

    :type results: dict, optional

    :rtype: dict

    :since: 1.0
    """

    users = tuple(users)
    results = OrderedDict() if results is None else results

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


def as_buildinfo(session, build):
    """
    Coerces a build value into a koji build info dict.

    If build is an
     * int, will attempt to load as a build ID
     * str, will attempt to load as an NVR
     * dict, will presume already a build info

    :param session: an active koji client session

    :param build: value to lookup

    :type build: int or str or dict

    :rtype: dict

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


def as_channelinfo(session, channel):
    """
    Coerces a channel value into a koji channel info dict.

    If channel is an
     * int, will attempt to load as a channel ID
     * str, will attempt to load as a channel name
     * dict, will presume already a channel info

    :param session: an active koji client session

    :param channel: value to lookup

    :rtype: dict

    :raises NoSuchChannel: if the channel could not be resolved

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


def as_taginfo(session, tag):
    """
    Coerces a tag value into a koji tag info dict.

    If tag is an
     * int, will attempt to load as a tag ID
     * str, will attempt to load as a tag name
     * dict, will presume already a tag info

    :param session: an active koji client session

    :param tag: value to lookup

    :type tag: int or str or dict

    :rtype: dict

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


def as_packageinfo(session, pkg):
    """
    Coerces a host value into a host info dict.

    If pkg is an:
     * int, will attempt to load as a package ID
     * str, will attempt to load as a package name
     * dict, will presume already a package info

    :param session: an active koji client session

    :param pkg: value to lookup

    :rtype: dict

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


def as_taskinfo(session, task):
    """
    Coerces a task value into a koji task info dict.

    If task is an
     * int, will attempt to load as a task ID
     * dict, will presume already a task info

    :param session: an active koji client session

    :param task: value to lookup

    :type task: int or dict

    :rtype: dict

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


def as_targetinfo(session, target):
    """
    Coerces a target value into a koji target info dict.

    If target is an
     * int, will attempt to load as a target ID
     * str, will attempt to load as a target name
     * dict, will presume already a target info

    :param session: an active koji client session

    :param target: value to lookup

    :type target: int or str or dict

    :rtype: dict

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


def as_hostinfo(session, host):
    """
    Coerces a host value into a host info dict.

    If target is an:
     * int, will attempt to load as a host ID
     * str, will attempt to load as a host name
     * dict, will presume already a host info

    :param session: an active koji client session

    :param host: value to lookup

    :type host: int or str or dict

    :rtype: dict

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


def as_archiveinfo(session, archive):
    """
    Coerces an archive value into an archive info dict.

    If archive is an:
     * int, will attempt to load as an archive ID
     * str, will attempt to load as an archive filename
     * dict, will presume already an archive info

    :param session: an active koji client session

    :param archive: value to lookup

    :type archive: int or str or dict

    :rtype: dict

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


def as_repoinfo(session, repo):
    """
    Coerces a repo value into a Repo info dict.

    If repo is an:
     * dict with name, will attempt to load the current repo from a
       tag by that name
     * str, will attempt to load the current repo from a tag by name
     * int, will attempt to load the repo by ID
     * dict, will presume already a repo info

    :param session: an active koji client session

    :param repo: repo to resolve

    :rtype: dict

    :raises NoSuchRepo: if the repo value could not be resolved to a
      repo info dict

    :since: 1.1
    """

    info = None

    if isinstance(repo, dict):
        if "name" in repo:
            repo = repo["name"]
        else:
            info = repo

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


def as_rpminfo(session, rpm):
    """
    Coerces a host value into a RPM info dict.

    If rpm is an:
     * int, will attempt to load as a RPM ID
     * str, will attempt to load as a RPM NVR
     * dict, will presume already an RPM info

    :param session: an active koji client session

    :param rpm: value to lookup

    :type rpm: int or str or dict

    :rtype: dict

    :raises NoSuchRPM: if the rpm value could not be resolved
      into a RPM info dict

    :since: 1.0
    """

    if isinstance(rpm, (str, int)):
        info = session.getRPM(rpm)
    elif isinstance(rpm, dict):
        info = rpm
    else:
        info = None

    if not info:
        raise NoSuchRPM(rpm)

    return info


def as_userinfo(session, user):
    """
    Resolves user to a userinfo dict.

    If user is a str or int, then getUser will be invoked. If user is
    already a dict, it's presumed to be a userinfo already and it's
    returned unaltered.

    :param session: an active koji client session

    :param user: Name, ID, or User Info describing a koji user

    :type user: str or int or dict

    :rtype: dict

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


def hub_version(session):
    """
    Wrapper for ``session.getKojiVersion`` which caches the results on
    the session and splits the value into a tuple of ints for easy
    comparison.

    If the getKojiVersion method isn't implemented on the hub, we
    presume that we're version 1.22 ``(1, 22)`` which is the last
    version before getKojiVersion was added.

    :param session: an active koji client session

    :rtype: tuple[int]

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


def version_check(session, minimum=(1, 23)):
    """
    Verifies that the requested minimum version is met compared
    against session.getKojiVersion.

    If the getKojiVersion method isn't implemented on the hub, we
    presume that we're version 1.22 (the last version before
    getKojiVersion was added). Because of this, checking for minimum
    versions lower than 1.23 will always return True.

    Version is specified as a tuple of integers, eg. 1.23 is ``(1,
    23)``

    :param session: an active koji client session

    :param minimum: Minimum version required. Default, ``(1, 23)``

    :type minimum: tuple[int]

    :rtype: bool

    :since: 1.0
    """

    if isinstance(minimum, str):
        minimum = tuple(map(_int, minimum.split(".")))

    hub_ver = hub_version(session)

    return bool(hub_ver and hub_ver >= minimum)


def version_require(session, minimum=(1, 23), message=None):
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

    :param session: an active koji client session

    :param minimum: Minimum version required. Default, ``(1, 23)``

    :type minimum: tuple[int]

    :param message: Message to use in exception if version check
      fails. Default, with a minimum of ``(1, 23)``, ``"requires >=
      1.23"``

    :type message: str, optional

    :raises FeatureUnavailable: If the minimum version is not met

    :rtype: bool

    :since: 1.0
    """

    if version_check(session, minimum=minimum):
        return True

    if message is None:
        if isinstance(minimum, (list, tuple)):
            minimum = ".".join(str(m) for m in minimum)
        message = "requires >= %s" % minimum

    raise FeatureUnavailable(message)


#
# The end.
