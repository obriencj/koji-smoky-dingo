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
Koji Smoky Dingo

Utility functions and command line plugins for Koji administrators.

author: Christopher O'Brien <obriencj@gmail.com>
license: GPL v3
"""


from collections import OrderedDict
from koji import convertFault, read_config, Fault, ClientSession
from koji_cli.lib import activate_session, ensure_connection
from six.moves import zip

from .common import chunkseq


class ManagedClientSession(ClientSession):
    """
    A koji.ClientSession that can be used as via the 'with' keyword to
    provide a managed session that will handle login and logout. Also
    takes care of loading the relevant profile configuration.
    """

    def __init__(self, profile="koji"):
        conf = read_config(profile)
        server = conf["server"]
        super(ManagedClientSession, self).__init__(server, opts=conf)

    def __enter__(self):
        activate_session(self, self.opts)
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        self.logout()
        if self.rsession:
            self.rsession.close()
            self.rsession = None
        return (exc_type is None)


class AnonClientSession(ManagedClientSession):
    """
    A koji.ClientSession that can be used as via the 'with' keyword to
    provide a managed session that will handle login and logout. Also
    takes care of loading the relevant profile configuration.
    """

    def __enter__(self):
        ensure_connection(self)
        return self


class BadDingo(Exception):
    complaint = "Something bad happened"

    def __str__(self):
        orig = super(BadDingo, self).__str__()
        return ": ".join([self.complaint, orig])


class NoSuchBuild(BadDingo):
    complaint = "No such build"


class NoSuchChannel(BadDingo):
    complaint = "No such builder channel"


class NoSuchContentGenerator(BadDingo):
    complaint = "No such content generator"


class NoSuchTag(BadDingo):
    complaint = "No such tag"


class NoSuchTask(BadDingo):
    complaint = "No such task"


class NoSuchUser(BadDingo):
    complaint = "No such user"


class NoSuchPermission(BadDingo):
    complaint = "No such permission"


class NotPermitted(BadDingo):
    complaint = "Insufficient permissions"


def _bulk_load(session, loadfn, keys, size):
    """
    Generator utility for multicall loading data from a koji client
    session.

    loadfn is a bound method which will be called with each key in the
    keys sequence. Up to size calls will be made at a time.

    Yields key, result pairs.

    Will convert any koji faults to exceptions and raise them.
    """

    for key_chunk in chunkseq(keys, size):
        session.multicall = True

        for key in key_chunk:
            # print(key, file=sys.stderr)
            loadfn(key)

        for key, info in zip(key_chunk, session.multiCall()):
            # print(key, info, file=sys.stderr)

            if info:
                if "faultCode" in info:
                    raise convertFault(Fault(**info))
                else:
                    yield key, info[0]
            else:
                yield key, None


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
    """

    results = OrderedDict() if results is None else results

    for key, info in _bulk_load(session, session.getBuild, nvrs, size):
        if err and not info:
            raise NoSuchBuild(key)
        else:
            results[key] = info

    return results


def bulk_load_tasks(session, tasks, err=True, size=100, results=None):
    results = OrderedDict() if results is None else results

    for key, info in _bulk_load(session, session.getTask, tasks, size):
        if err and not info:
            raise NoSuchTask(key)
        else:
            results[key] = info

    return results


def bulk_load_tags(session, tags, err=True, size=100, results=None):
    results = OrderedDict() if results is None else results

    for key, info in _bulk_load(session, session.getTag, tags, size):
        if err and not info:
            raise NoSuchTag(key)
        else:
            results[key] = info

    return results


def bulk_load_rpm_sigs(session, rpm_ids, size=100, results=None):
    results = OrderedDict() if results is None else results

    for key, info in _bulk_load(session, session.queryRPMSigs, rpm_ids, size):
        results[key] = info

    return results


#
# The end.
