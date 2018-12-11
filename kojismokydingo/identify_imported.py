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
Koji Smoky Dingo - info command identify-imported

Given a tag or a list of builds, identify which of those were imported
(vs. actually build in koji)

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

from . import AnonSmokyDingo, NoSuchTag, \
    mass_load_builds, read_clean_lines, unique


def identify_imported(build_infos, negate=False, by_cg=set()):
    """
    Given a sequence of build info dicts, yield those which are imports.

    if negate is True, then behavior is flipped and only non-imports
    are emitted (and the by_cg parameter is ignored)

    If by_cg is not specified, then only non CG imports are emitted.
    If by_cg is specified, then emit only those imports which are from
    a content generator in that set (or all content generators if
    'all' is in the by_cg set).
    """

    all_cg = "all" in by_cg

    for build in build_infos:
        extra = build.get("extra", None)
        build_cg = extra.get("build_system", None) if extra else None

        is_import = build.get("task_id", None) is None

        if negate:
            # looking for non-imports, regardless of CG or not
            if not is_import:
                yield build

        elif is_import:
            if build_cg:
                if all_cg or build_cg in by_cg:
                    # this is a CG import, and we wanted either this
                    # specific one or all of them
                    yield build

            elif not by_cg:
                # this isn't a CG import, and we didn't want it to be
                yield build


def cli_identify_imported(session, tagname=None, nvr_list=None,
                          inherit=False, negate=False,
                          cg_list=()):

    if nvr_list:
        builds = mass_load_builds(session, unique(nvr_list))

    elif tagname:
        taginfo = session.getTag(tagname)
        if not taginfo:
            raise NoSuchTag(tagname)

        builds = session.listTagged(taginfo["id"], inherit=inherit)

        if not negate:
            # the listTagged call doesn't return the extra information
            # we need to determine which CG something came from, so we
            # need to gather up full buildinfo data from those results
            # first.  However we happen to know that in negate mode
            # we don't actually care about that, so we'll skip the
            # loading in that case.
            bids = (b["id"] for b in builds)
            builds = mass_load_builds(session, bids)

    else:
        # from the CLI, one of these should be specified.
        builds = ()

    for build in identify_imported(builds, negate, cg_list):
        print(build["nvr"])


class cli(AnonSmokyDingo):

    description = "Detect imported builds"


    def parser(self):
        argp = super(AnonSmokyDingo, self).parser()

        group = argp.mutually_exclusive_group()
        addarg = group.add_argument

        addarg("tag", nargs="?", action="store", default=None,
               metavar="TAGNAME",
               help="Tag containing builds to check.")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Set to - to read from stdin.")

        addarg = argp.add_argument

        addarg("-i", "--inherit", action="store_true", default=False,
               help="also scan any parent tags when checking"
               " for imported builds")

        addarg("-n", "--negate", action="store_true", default=False,
               help="inverted behavior, list non-imports instead"
               " of imports")

        addarg("-c", "--content-generator", dest="cg_list",
               action="append", default=list(),
               metavar="CG_NAME",
               help="show content generator imports by build"
               " system name. Default: display no CG builds."
               " Specify 'all' to see CG imports from any system."
               " May be specified more than once.")

        return argp


    def validate(self, parser, options):
        if not (options.tag or options.nvr_file):
            parser.error("Please specify either a tag to scan, or"
                         " --file=NVR_FILE")


    def handle(self, options):
        nvr_list = read_clean_lines(options.nvr_file)

        return cli_identify_imported(options.session, options.tag,
                                     nvr_list,
                                     options.inherit, options.negate,
                                     options.cg_list)


#
# The end.
