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


import os

from six import iteritems

from . import AnonLonelyDingo
from ..cli import find_action, printerr, resplit
from ..cli.builds import FilterBuilds
from ..sift import Sifter, SifterError


__all__ = (
    "LonelyFilterBuilds",
    "ksd_filter_builds",
)


class LonelyFilterBuilds(AnonLonelyDingo, FilterBuilds):
    """
    Adapter to make the FilterBuilds command into a LonelyDingo.
    """

    def arguments(self, parser):
        addarg = parser.add_argument
        addarg("filter_file", metavar="FILTER_FILE",
               help="File of sifty filter predicates")

        parser = self.profile_arguments(parser)
        return super(LonelyFilterBuilds, self).arguments(parser)


    def sifter_arguments(self, parser):
        grp = parser.add_argument_group("Filtering with Sifty sieves")
        addarg = grp.add_argument

        addarg("--output", "-o", action="append", default=list(),
               dest="outputs", metavar="FLAG=FILENAME",
               help="Divert results marked with the given FLAG to"
               " FILENAME. If FILENAME is '-', output to stdout."
               " The 'default' flag is output to stdout by default,"
               " and other flags are discarded")

        addarg("--param", "-P", action="append", default=list(),
               dest="params", metavar="KEY=VALUE",
               help="Provide compile-time values to the sifty"
               " filter expressions")

        addarg("--env", action="store_true", default=False,
               dest="use_env",
               help="Use environment vars for params left unassigned")

        return parser


    def get_sifter(self, options):
        return Sifter(self.get_sieves(), options.filter,
                      params=options.params)


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

        # some options can be specified multiple times, so don't use a
        # dict
        defaults = []
        params = []
        for line in src.splitlines():
            if line.startswith("#option "):
                defn = line[8:].split("=", 1)
                key = defn[0].strip()
                val = "" if len(defn) == 1 else defn[1].strip()
                defaults.append((key, val))

            elif line.startswith("#param "):
                defn = line[7:].split("=", 1)
                key = defn[0].strip()
                val = None if len(defn) == 1 else defn[1].srip()
                params.append((key, val))

        for key, val in defaults:
            act = find_action(parser, key)
            if not act:
                printerr("WARNING: unknown option", key)

            elif getattr(options, act.dest) == act.default:
                # FIXME: this heuristic isn't very good. we're
                # checking if the options object has what would be the
                # default value, and presuming that means it wasn't
                # set to anything, and therefore setting it to the
                # value of the define in the script. However, this
                # means one cannot use a command-line switch to
                # override a define back to its default
                # value. Something to fix later.
                act(parser, options, val)

        # build up a params dict based on command-line options, param
        # definitions from the filter file, and finally the
        # environment if the --env flag was set.
        cli_params = options.params
        env_params = os.environ if options.use_env else {}
        params = dict(params)

        for opt in resplit(cli_params):
            if "=" in opt:
                key, val = opt.split("=", 1)
            else:
                key = opt
                val = None

            if key not in params:
                printerr("WARNING: unexpected param", key)
            else:
                params[key] = val

        for key, val in iteritems(params):
            if val is None:
                if key in env_params:
                    params[key] = env_params[key]
                else:
                    msg = "param %s is not defined" % key
                    raise SifterError(msg)

        options.params = params

        return super(LonelyFilterBuilds, self).validate(parser, options)


# The console_scripts entry point is an instance of the class, not the
# class itself.
ksd_filter_builds = LonelyFilterBuilds("ksd-filter-builds")


# The end.
