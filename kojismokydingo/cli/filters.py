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


import sys

from argparse import ArgumentParser
from koji import GenericError
from os.path import basename
from six import iteritems

from .. import AnonClientSession, BadDingo
from . import AnonSmokyDingo, printerr
from .builds import FilterBuilds


def find_action(parser, key):
    for act in parser._actions:
        if act.metavar == key:
            return act
        elif act.dest == key:
            return act
    return None


class FilterCLI(AnonSmokyDingo):
    """
    An adaptive layer to move a BuildFilter command into a stand-alone
    CLI entry point
    """


    def arguments(self, parser):
        addarg = parser.add_argument
        addarg("filter_file", metavar="FILTER_FILE",
               help="File of sifty filter predicates")

        parser = self.profile_arguments(parser)
        return super(FilterCLI, self).arguments(parser)


    def profile_arguments(self, parser):
        grp = parser.add_argument_group("Koji Profile options")
        addarg = grp.add_argument

        addarg("--profile", "-p", action="store", default=None,
               metavar="PROFILE", help="specify a configuration profile")

        return parser


    def sifter_arguments(self, parser):
        grp = parser.add_argument_group("Filtering with Sifty sieves")
        addarg = grp.add_argument

        addarg("--output", "-o", action="append", default=list(),
               dest="outputs", metavar="FLAG=FILENAME",
               help="Divert results marked with the given FLAG to"
               " FILENAME. If FILENAME is '-', output to stdout."
               " The 'default' flag is output to stdout by default,"
               " and other flags are discarded")

        return parser


    def parser(self):
        invoke = basename(sys.argv[0])
        argp = ArgumentParser(prog=invoke, description=self.description)
        return self.arguments(argp) or argp


    def validate(self, parser, options):
        # we need to go through the filter_file to look for the define
        # directives, which is not part of the normal sifty filtering
        # language. Since we're doing so, we may as well just load the
        # filter into memory and use it for the sifter parsing as well,
        # so we'll set filter_file to None and filter to the contents.

        with open(options.filter_file, "rt") as fin:
            src = fin.read()

        options.filter_file = None
        options.filter = src

        definitions = {}
        for line in src.splitlines():
            if line.startswith("#define "):
                defn = line[8:].split("=", 1)
                key = defn[0].strip()
                val = "" if len(defn) == 1 else defn[1].strip()
                definitions[key] = val

        for key, val in iteritems(definitions):
            act = find_action(parser, key)
            if not act:
                printerr("WARNING: unknown option", key)

            elif getattr(options, act.dest) == act.default:
                act(parser, options, val)

        return super(FilterCLI, self).validate(parser, options)


    def __call__(self):

        called = sys.argv[0]
        args = sys.argv[1:]

        parser = self.parser()
        options = parser.parse_args(args)

        self.validate(parser, options)

        try:
            with AnonClientSession(options.profile) as session:
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


class KSDFilterBuilds(FilterCLI, FilterBuilds):
    pass


ksd_filter_builds = KSDFilterBuilds("ksd-filter-builds")


#
# The end.