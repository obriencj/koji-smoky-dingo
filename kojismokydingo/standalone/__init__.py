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
Koji Smoky Dingo - Standalone

This package contains adaptive mechanisms for converting a SmokyDingo command
into a stand-alone console_script entry point.

:author: Christopher O'Brien <obriencj@gmail.com>
:licence: GPL v3
"""


import sys

from argparse import ArgumentParser
from koji import GenericError
from os.path import basename
from typing import List

from .. import (
    AnonClientSession, BadDingo, ManagedClientSession,
    ProfileClientSession, )
from ..cli import AnonSmokyDingo, SmokyDingo, printerr


__all__ = (
    "AnonLonelyDingo",
    "LonelyDingo",
)


class LonelyDingo(SmokyDingo):
    """
    An adaptive layer to assist in converting a SmokyDingo instance
    into a callable suitable for use as a console_scripts entry point.
    """


    default_profile: str = None
    """
    when set this becomes the default value for the ``--profile=``
    argument added to argument parser
    """


    @classmethod
    def main(cls, name: str = None, args: List[str] = None) -> int:
        return cls(name)(args)


    def create_session(self, profile: str) -> ManagedClientSession:
        return ProfileClientSession(profile)


    def parser(self):
        invoke = basename(sys.argv[0])
        argp = ArgumentParser(prog=invoke, description=self.description)
        argp = self.profile_arguments(argp) or argp
        return self.arguments(argp) or argp


    def profile_arguments(self, parser: ArgumentParser) -> ArgumentParser:
        grp = parser.add_argument_group("Koji Profile options")
        addarg = grp.add_argument

        profile = self.default_profile
        required = profile is None

        addarg("--profile", "-p", action="store", metavar="PROFILE",
               default=profile, required=required,
               help="specify a configuration profile")

        return parser


    def __call__(self, args=None):

        # TODO: mypy hates that the method signature changes here, and
        # it might be right about that being a problem. Look into
        # it...

        parser = self.parser()
        options = parser.parse_args(args)

        self.validate(parser, options)

        try:
            with self.create_session(options.profile) as session:
                self.session = session
                self.pre_handle(options)
                return self.handle(options) or 0

        except KeyboardInterrupt:
            printerr()
            return 130

        except GenericError as kge:
            printerr(kge)
            return -1

        except BadDingo as bad:
            printerr(bad)
            return -2

        except Exception:
            # koji CLI hides tracebacks from us. If something goes
            # wrong, we want to see it
            import traceback
            traceback.print_exc()
            raise

        finally:
            self.session = None


class AnonLonelyDingo(LonelyDingo):
    """
    An adaptive layer to assist in converting an AnonSmokyDingo
    instance into a callable suitable for use as a console_scripts
    entry point.
    """

    def create_session(self, profile: str) -> ManagedClientSession:
        return AnonClientSession(profile)


#
# The end.
