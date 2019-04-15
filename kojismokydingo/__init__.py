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


from __future__ import print_function

import re
import sys

from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from collections import OrderedDict
from functools import partial
from koji import convertFault, Fault, GenericError
from koji_cli.lib import activate_session
from os.path import basename
from six import add_metaclass
from six.moves import \
    range as xrange, \
    zip as izip, \
    zip_longest as izip_longest


class BadDingo(Exception):
    complaint = "Something bad"

    def __str__(self):
        orig = super(BadDingo, self).__str__()
        return ": ".join([self.complaint, orig])


class NoSuchBuild(BadDingo):
    complaint = "No such build"


class NoSuchTag(BadDingo):
    complaint = "No such tag"


class NoSuchTask(BadDingo):
    complaint = "No such task"


class NoSuchUser(BadDingo):
    complaint = "No such user"


class PermissionException(BadDingo):
    complaint = "Insufficient permissions"


printerr = partial(print, file=sys.stderr)


def unique(sequence):
    return list(OrderedDict.fromkeys(sequence))


def chunkseq(seq, chunksize):
    try:
        seqlen = len(seq)
    except TypeError:
        seq = list(seq)
        seqlen = len(seq)

    return (seq[offset:offset + chunksize] for
            offset in xrange(0, seqlen, chunksize))


def _rpm_str_split(s, _split=re.compile(r"(~?(?:\d+|[a-zA-Z]+))").split):
    """
    Split an E, V, or R string for comparison by its segments
    """

    return tuple(i for i in _split(s) if (i.isalnum() or i.startswith("~")))


def _rpm_str_compare(left, right):
    left = _rpm_str_split(left)
    right = _rpm_str_split(right)

    for lp, rp in izip_longest(left, right, fillvalue=""):

        # Special comparison for tilde segments
        if lp.startswith("~"):
            # left is tilde

            if rp.startswith("~"):
                # right also is tilde, let's just chop off the tilde
                # and fall through to non-tilde comparisons below

                lp = lp[1:]
                rp = rp[1:]

            else:
                # right is not tilde, therefore right is greater
                return -1

        elif rp.startswith("~"):
            # left is not tilde, but right is, therefore left is greater
            return 1

        # Special comparison for digits vs. alphabetical
        if lp.isdigit():
            # left is numeric

            if rp.isdigit():
                # left and right are both numeric, convert and fall
                # through
                lp = int(lp)
                rp = int(rp)

            else:
                # right is alphabetical or absent, left is greater
                return 1

        elif rp.isdigit():
            # left is alphabetical but right is not, right is greater
            return -1

        # Final comparison for segment
        if lp == rp:
            # left and right are equivalent, check next segment
            continue
        else:
            # left and right are not equivalent
            return 1 if lp > rp else -1

    else:
        # ran out of segments to check, must be equivalent
        return 0


def rpm_evr_compare(left_evr, right_evr):
    """
    Compare two (Epoch, Version, Release) tuples.

    Returns  1 if left_evr is greater-than right_evr
             0 if left_evr is equal-to right_evr
            -1 if left_evr is less-than right_evr
    """

    for lp, rp in izip_longest(left_evr, right_evr, fillvalue="0"):
        if lp == rp:
            # fast check to potentially skip all the matching
            continue

        compared = _rpm_str_compare(lp, rp)
        if compared:
            # non zero comparison for segment, done checking
            return compared

    else:
        # ran out of segments to check, must be equivalent
        return 0


class NEVRCompare(object):
    """
    An adapter for Name, Epoch, Version, Release comparisons of a
    build info dictionary. Used by the nevr_sort_builds function.
    """

    def __init__(self, binfo):
        self.build = binfo
        self.n = binfo["name"]

        evr = (binfo["epoch"], binfo["version"], binfo["release"])
        self.evr = tuple(("0" if x is None else str(x)) for x in evr)


    def __cmp__(self, other):
        # cmp is a python2-ism, and has no replacement in python3 via
        # six, so we'll have to create our own simplistic behavior
        # similarly

        if self.n == other.n:
            return rpm_evr_compare(self.evr, other.evr)

        elif self.n < other.n:
            return -1

        else:
            return 1


    def __eq__(self, other):
        return self.__cmp__(other) == 0


    def __lt__(self, other):
        return self.__cmp__(other) < 0


    def __gt__(self, other):
        return self.__cmp__(other) > 0


def nevr_sort_builds(build_infos):
    """
    Given a sequence of build info dictionaries, sort them by Name,
    Epoch, Version, and Release using RPM's variation of comparison
    """

    return sorted(build_infos, key=NEVRCompare)


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

        for key, info in izip(key_chunk, session.multiCall()):
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


def read_clean_lines(filename="-"):

    if not filename:
        return []

    elif filename == "-":
        fin = sys.stdin

    else:
        fin = open(filename, "r")

    lines = [line for line in (l.strip() for l in fin) if line]
    # lines = list(filter(None, map(str.strip, fin)))

    if filename != "-":
        fin.close()

    return lines


@add_metaclass(ABCMeta)
class SmokyDingo(object):

    group = "cli"
    description = "A CLI Plugin"

    # this is necessary for koji to recognize us as a cli command
    exported_cli = True


    def __init__(self, name):
        self.name = name

        # these will be populated once the command instance is
        # actually called
        self.goptions = None
        self.session = None

        # this is used to register the command with koji in a manner
        # that it expects to deal with
        self.__name__ = "handle_" + name.replace("-", "_")

        # allow a docstr to be specified on subclasses, but if absent
        # let's set it based on the group and description.
        if getattr(self, "__doc__", None) is None:
            self.__doc__ = "[%s] %s" % (self.group, self.description)


    def parser(self):
        """
        Override to provide an ArgumentParser instance with all the
        relevant positional arguments and options added.
        """

        invoke = " ".join((basename(sys.argv[0]), self.name))
        return ArgumentParser(prog=invoke, description=self.description)


    def validate(self, parser, options):
        """
        Override to perform validation on options values. Return value is
        ignored, use parser.error if needed.
        """

        pass


    def pre_handle(self, options):
        """
        Used by admin commands to authenticate. Does nothing normally.
        """

        pass


    @abstractmethod
    def handle(self, options):
        """
        Perform the full set of actions for this command.
        """

        pass


    def __call__(self, goptions, session, args):
        self.goptions = goptions
        self.session = session

        parser = self.parser()
        options = parser.parse_args(args)

        self.validate(parser, options)

        try:
            activate_session(session, goptions)

            self.pre_handle(options)
            return self.handle(options) or 0

        except KeyboardInterrupt:
            print(file=sys.stderr)
            return 130

        except GenericError as kge:
            printerr(kge)
            return -1

        except BadDingo as bad:
            printerr(bad)
            return -2

        except Exception:
            import traceback
            traceback.print_exc()
            raise


class AdminSmokyDingo(SmokyDingo):

    group = "admin"


    def pre_handle(self, options):
        # before attempting to actually perform the command task,
        # ensure that the user has the appropriate admin permissions,
        # to prevent it failing at a strange point

        session = self.session

        userinfo = session.getLoggedInUser()
        userperms = session.getUserPerms(userinfo["id"]) or ()

        if "admin" not in userperms:
            msg = "command %s requires admin permissions" % self.name
            raise PermissionException(msg)


class AnonSmokyDingo(SmokyDingo):

    group = "info"


    def __init__(self, name):
        super(AnonSmokyDingo, self).__init__(name)
        self.__name__ = "anon_handle_" + self.name.replace("-", "_")


#
# The end.
