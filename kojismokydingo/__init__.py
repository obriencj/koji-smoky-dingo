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


from __future__ import print_function

import sys

from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from collections import OrderedDict
from functools import partial
from koji import GenericError
from koji_cli.lib import activate_session
from os.path import basename
from six import add_metaclass
from six.moves import range as xrange, zip as izip


class BadDingo(Exception):
    complaint = "Something bad"


class NoSuchTag(BadDingo):
    complaint = "No such tag"


class NoSuchBuild(BadDingo):
    complaint = "No such build"


class NoSuchUser(BadDingo):
    complaint = "No such user"


class PermissionException(BadDingo):
    complaint = "Insufficient permissions"


printerr = partial(print, file=sys.stderr)


def unique(sequence):
    return list(OrderedDict((s, None) for s in sequence))


def chunkseq(seq, chunksize):
    return (seq[offset:offset + chunksize] for
            offset in xrange(0, len(seq), chunksize))


def mass_load_builds(session, nvrs, nsbfn=None, size=100):

    results = []

    # nsbfn is a unary function meant to deal with an NVR which didn't
    # return a build info. Calling functions can use this to collect
    # malformed or missing builds, or to raise an exception. If
    # unspecified, then missing builds are just skipped.

    for nvr_chunk in chunkseq(nvrs, size):
        session.multicall = True

        for nvr in nvr_chunk:
            session.getBuild(nvr)

        for nvr, binfo in izip(nvr_chunk, session.multiCall()):
            if binfo:
                if "faultCode" in binfo:
                    # koji returned an error dict instead of a list of
                    # builds, invoke the nsbfn if it exists, to signal
                    # no such build was found
                    nsbfn and nsbfn(nvr)
                else:
                    # otherwise it returned a list of matching builds
                    # (usually just 1, but let's make sure)
                    for b in binfo:
                        if not b:
                            # invoke the nsbfn if it exists, to signal
                            # no such build was found
                            nsbfn and nsbfn(nvr)
                        else:
                            results.append(b)
            else:
                # koji's multicall shouldn't return an empty list, but
                # just in case, treat it as a missing build
                nsbfn and nsbfn(nvr)

    return results


def read_clean_lines(filename="-"):

    if not filename:
        return []

    elif filename == "-":
        fin = sys.stdin

    else:
        fin = open(filename, "r")

    lines = [line for line in (l.strip() for l in fin) if line]

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
        invoke = " ".join((basename(sys.argv[0]), self.name))
        return ArgumentParser(prog=invoke, description=self.description)


    def pre_handle(self, options):
        pass


    @abstractmethod
    def handle(self, options):
        pass


    def validate(self, parser, options):
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
            printerr(": ".join((bad.complaint, str(bad))))
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
