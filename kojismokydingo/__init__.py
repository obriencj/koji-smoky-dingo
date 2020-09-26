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
from koji import convertFault, read_config, Fault, ClientSession
from koji_cli.lib import activate_session, ensure_connection
from six.moves import zip

from .common import chunkseq


class ManagedClientSession(ClientSession):
    """
    A `koji.ClientSession` that can be used as via the ``with``
    keyword to provide a managed session that will handle
    authenticated login and logout.
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
    """

    def __init__(self, profile="koji", anon=False):
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
    """

    complaint = "Something bad happened"

    def __str__(self):
        orig = super(BadDingo, self).__str__()
        return ": ".join([self.complaint, orig])


class NoSuchBuild(BadDingo):
    """
    A build was not found
    """

    complaint = "No such build"


class NoSuchChannel(BadDingo):
    """
    A channel was not found
    """

    complaint = "No such builder channel"


class NoSuchContentGenerator(BadDingo):
    """
    A content generator was not found
    """

    complaint = "No such content generator"


class NoSuchTag(BadDingo):
    """
    A tag was not found
    """

    complaint = "No such tag"


class NoSuchTarget(BadDingo):
    """
    A target was not found
    """

    complaint = "No such target"


class NoSuchTask(BadDingo):
    """
    A task was not found
    """

    complaint = "No such task"


class NoSuchUser(BadDingo):
    """
    A user was not found
    """

    complaint = "No such user"


class NoSuchPermission(BadDingo):
    """
    A permission was not found
    """

    complaint = "No such permission"


class NotPermitted(BadDingo):
    """
    A required permission was not associated with the currently logged
    in user account.
    """

    complaint = "Insufficient permissions"


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
    support dict assignment, and will be used in place of a newly
    allocated `OrderedDict` to store and return the results.

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
      support item assignment (like a dict), and it will be populated
      and then used as the return value for this function. Default, a
      new `OrderedDict` will be allocated.

    :type results: dict, optional

    :raises koji.GenericError: if `err` is `True` and an issue
      occurrs while invoking the `loadfn`

    :rtype: dict[object, object]
    """

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, loadfn, keys, err, size):
        results[key] = info

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
      bad or missing NVRs will be absent from the results mapping.

    :type err: bool, optional

    :param size: Count of NVRs to load in a single multicall. Default,
      100

    :type size: int, optional
    """

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, session.getBuild, nvrs,
                                    False, size):
        if not info:
            if err:
                raise NoSuchBuild(key)
        else:
            results[key] = info

    return results


def bulk_load_tasks(session, task_ids, request=False,
                    err=True, size=100, results=None):

    results = OrderedDict() if results is None else results

    fn = partial(session.getTaskInfo, request=request)

    for key, info in iter_bulk_load(session, fn, task_ids, False, size):
        if not info:
            if err:
                raise NoSuchTask(key)
        else:
            results[key] = info

    return results


def bulk_load_tags(session, tags, err=True, size=100, results=None):

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, session.getTag, tags,
                                    False, size):
        if not info:
            if err:
                raise NoSuchTag(key)
        else:
            results[key] = info

    return results


def bulk_load_rpm_sigs(session, rpm_ids, size=100, results=None):
    """
    Set up a chunking multicall to fetch the signatures for a list of
    RPM via session.queryRPMSigs for each ID in rpm_ids.

    Returns an OrderedDict associating the individual RPM IDs with their
    resulting RPM signature lists.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated OrderedDict to store and
    return the results.
    """

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, session.queryRPMSigs,
                                    rpm_ids, True, size):
        results[key] = info

    return results


def bulk_load_buildroot_archives(session, buildroot_ids, btype=None,
                                 size=100, results=None):

    results = OrderedDict() if results is None else results

    fn = lambda i: session.listArchives(componentBuildrootID=i, type=btype)

    for key, info in iter_bulk_load(session, fn, buildroot_ids, True, size):
        results[key] = info

    return results


def bulk_load_buildroot_rpms(session, buildroot_ids,
                             size=100, results=None):

    results = OrderedDict() if results is None else results

    fn = lambda i: session.listRPMs(componentBuildrootID=i)

    for key, info in iter_bulk_load(session, fn, buildroot_ids, True, size):
        results[key] = info

    return results


def bulk_load_build_archives(session, build_ids, btype=None,
                             size=100, results=None):
    """
    Set up a chunking multicall to fetch the the archives of builds
    via session.listArchives for each build ID in build_ids.

    Returns an OrderedDict associating the individual build IDs with
    their resulting archive lists.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated OrderedDict to store and
    return the results.
    """

    results = OrderedDict() if results is None else results

    fn = lambda i: session.listArchives(buildID=i, type=btype)

    for key, info in iter_bulk_load(session, fn, build_ids, True, size):
        results[key] = info

    return results


def bulk_load_build_rpms(session, build_ids, size=100, results=None):
    """
    Set up a chunking multicall to fetch the the archives of builds
    via session.listArchives for each build ID in build_ids.

    Returns an OrderedDict associating the individual build IDs with
    their resulting archive lists.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated OrderedDict to store and
    return the results.
    """

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, session.listRPMs,
                                    build_ids, True, size):
        results[key] = info

    return results


def bulk_load_buildroots(session, broot_ids, size=100, results=None):
    """
    Set up a chunking multicall to fetch the buildroot data via
    session.getBuildroot for each ID in broot_ids.

    Returns an OrderedDict associating the individual buildroot IDs
    with their resulting buildroot info dicts.

    If results is non-None, it must support dict assignment, and will
    be used in place of a newly allocated OrderedDict to store and
    return the results.
    """

    results = OrderedDict() if results is None else results

    for key, info in iter_bulk_load(session, session.getBuildroot,
                                    broot_ids, True, size):
        results[key] = info

    return results


def as_buildinfo(session, build):
    """
    Coerces a build value into a koji build info dict.

    If build is an
     * int, will attempt to load as a build ID
     * str, will attempt to load as an NVR
     * dict, will presume already a build info

    :param build: value to lookup

    :type build: int or str or dict

    :raises NoSuchBuild: if the build value could not be resolved
      into a build info dict

    :rtype: dict
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


def as_taginfo(session, tag):
    """
    Coerces a tag value into a koji tag info dict.

    If tag is an
     * int, will attempt to load as a tag ID
     * str, will attempt to load as a tag name
     * dict, will presume already a tag info

    :param tag: value to lookup

    :type tag: int or str or dict

    :raises NoSuchTag: if the tag value could not be resolved into a
      tag info dict

    :rtype: dict
    """

    if isinstance(tag, (str, int)):
        info = session.getTag(tag)
    elif isinstance(tag, dict):
        info = tag
    else:
        info = None

    if not info:
        raise NoSuchTag(tag)

    return info


def as_targetinfo(session, target):
    """
    Coerces a target value into a koji target info dict.

    If target is an
     * int, will attempt to load as a target ID
     * str, will attempt to load as a target name
     * dict, will presume already a target info

    :param target: value to lookup

    :type target: int or str or dict

    :raises NoSuchTarget: if the target value could not be resolved
      into a target info dict

    :rtype: dict
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


#
# The end.
