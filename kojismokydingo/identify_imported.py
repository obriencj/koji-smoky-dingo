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


import sys


def identify_imports(build_infos, reverse=False, by_cg=set()):
    """
    Given a sequence of build info dicts, emit those which are imports.

    if reverse is True, then behavior is flipped and only non-imports
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

        if reverse:
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


def chunk(seq, chunksize):
    return (seq[offset:offset+chunksize] for
            offset in xrange(0, len(seq), chunksize))


def chunk_load(session, build_ids):
    """
    Try not to be cruel to brew, and only request 100 build info at a
    time
    """

    for bid_chunk in chunk(build_ids, 100):
        multicall = MultiCall(session)
        for bid in bid_chunk:
            multicall.getBuild(bid)
        for binfo in multicall():
            yield binfo


def cli(options, nvr_list):

    session = ServerProxy(options.session)

    if len(nvr_list) == 1 and nvr_list[0] == "-":
        # special case, read list of NVRs from stdin
        nvr_list = (line.strip() for line in sys.stdin)
        nvr_list = [line for line in nvr_list if line]
        found_builds = list(chunk_load(session, nvr_list))

    elif nvr_list:
        found_builds = list(chunk_load(session, nvr_list))

    else:
        found_builds = list()

    if options.tag:
        call_args = {'__starstar': True,
                     'latest': False,
                     'inherit': options.inherit, }

        more_builds = session.listTagged(options.tag, call_args)

        if not options.reverse:
            # the listTagged call doesn't return the extra information
            # we need to determine which CG something came from, so we
            # need to gather up full buildinfo data from those results
            # first.  However we happen to know that in reverse mode
            # we don't actually care about that, so we'll skip the
            # loading in that case.
            more_builds = chunk_load(session, [b["id"] for b in more_builds])

        found_builds.extend(more_builds)

    matching = identify_imports(found_builds,
                                options.reverse,
                                set(options.cg))

    for build in matching:
        print build["nvr"]


class cli(AnonSmokyDingo):

    def parser(self):
        argp = super(AnonSmokyDingo, self).parser()
        addarg = argp.add_argument

        addarg("tag", nargs="*", action="append", default=[],
               metavar="TAGNAME",
               help="Tag containing builds to check.")

        addarg("-f", "--file", action="store", default=None,
               help="Read list of builds from file, one NVR per line."
               " Set to - to read from stdin.")

        addarg("-i", "--inherit", action="store_true", default=False,
               help="use with --tag=TAG to follow inheritance"
               " when searching for imported builds")

        addarg("-n", "--negate", action="store_true", default=False,
               help="inverted behavior, list non-imports instead"
               " of imports")

        addarg("-c", "--content-generator", action="append", default=list(),
               help="show content generator imports by build"
               " system name. Default: display no CG builds."
               " Specify 'all' to see CG imports from any system."
               " May be specified more than once.")

        return parse


    def handle(self, options):
        nvrs = read_builds(options)

        return cli_identify_imported(options.session, options.nvrs,
                                     options.


#
# The end.
