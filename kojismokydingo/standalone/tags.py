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
Koji Smoky Dingo - Standalone tag commands

:author: Christopher O'Brien <obriencj@gmail.com>
:licence: GPL v3
"""


from . import AnonLonelyDingo
from ..cli import find_action, printerr, remove_action, resplit
from ..cli.tags import FilterTags


__all__ = (
    "LonelyFilterTags",
    "ksd_filter_tags",
)


class LonelyFilterTags(AnonLonelyDingo, FilterTags):
    """
    Adapter to make the FilterTags command into a LonelyDingo.
    """

    def __init__(self, name=None):
        super().__init__(name)

        # some trickery to un-require the --profile option, though we
        # will mimic the behavior later. We need to do this because
        # this standalone may pull a profile out of the filter file
        # itself. We'll make sure to fail empty profile values later
        # in validation.
        self.default_profile = ""


    def arguments(self, parser):
        addarg = parser.add_argument
        addarg("filter_file", metavar="FILTER_FILE",
               help="File of sifty filter predicates")

        return super().arguments(parser)


    def sifter_arguments(self, parser):
        parser = super().sifter_arguments(parser)
        remove_action(parser, "--filter")
        remove_action(parser, "--filter-file")
        return parser


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

        if not options.profile:
            parser.error("the following arguments are required:"
                         " --profile/-p")

        self.default_params().update(params)

        return super().validate(parser, options)


ksd_filter_tags = LonelyFilterTags.main


#
# The end.
