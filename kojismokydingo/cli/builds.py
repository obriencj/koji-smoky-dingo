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
Koji Smoky Dingo - CLI Build Commands

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import sys

from argparse import ArgumentParser, Namespace
from functools import partial
from itertools import chain
from koji import ClientSession
from operator import itemgetter
from os import system
from shlex import quote
from typing import (
    Any, Callable, Dict, Iterable, List, Optional, Sequence, Union, )

from . import (
    AnonSmokyDingo, BadDingo, TagSmokyDingo,
    int_or_str, pretty_json, open_output,
    printerr, read_clean_lines, resplit, )
from .sift import BuildSifting, Sifter, output_sifted
from .. import (
    as_buildinfo, as_taginfo, as_userinfo,
    bulk_load, bulk_load_builds, bulk_load_tags, iter_bulk_load,
    version_check, )
from ..builds import (
    BuildFilter,
    build_dedup, build_id_sort, build_nvr_sort,
    decorate_builds_btypes, decorate_builds_cg_list,
    gather_component_build_ids, gather_wrapped_builds,
    iter_bulk_move_builds, iter_bulk_tag_builds,
    iter_bulk_untag_builds, )
from ..common import chunkseq, unique
from ..tags import ensure_tag, gather_tag_ids
from ..types import (
    BTypeInfo, BuildInfo, BuildInfos, BuildSpec,
    BuildState, DecoratedBuildInfo, GOptions, TagSpec, )
from ..users import collect_cgs


__all__ = (
    "BuildFiltering",
    "BulkMoveBuilds",
    "BulkTagBuilds",
    "BulkUntagBuilds",
    "FilterBuilds",
    "ListBTypes",
    "ListCGs",
    "ListComponents",
    "PullContainer",

    "cli_bulk_move_builds",
    "cli_bulk_tag_builds",
    "cli_bulk_untag_builds",
    "cli_filter_builds",
    "cli_list_btypes",
    "cli_list_cgs",
    "cli_list_components",
    "cli_pull_container",
)


SORT_BY_ID = "sort-by-id"
SORT_BY_NVR = "sort-by-nvr"


def cli_bulk_tag_builds(
        session: ClientSession,
        tagname: str,
        nvrs: Sequence[Union[int, str]],
        sorting: Optional[str] = None,
        owner: Optional[Union[int, str]] = None,
        inherit: bool = False,
        force: bool = False,
        notify: bool = False,
        create: bool = False,
        verbose: bool = False,
        strict: bool = False) -> None:

    """
    Implements the ``koji bulk-tag-builds`` command
    """

    # set up the verbose debugging output function
    if verbose:
        debug = printerr
    else:
        def debug(message):  # type: ignore
            pass

    # fetch the destination tag info (and make sure it actually
    # exists)
    taginfo = ensure_tag(session, tagname) if create \
        else as_taginfo(session, tagname)

    tagid = taginfo["id"]

    # figure out how we're going to be dealing with builds that don't
    # have a matching pkg entry already. Someone needs to own them...
    ownerid = None
    if owner:
        ownerinfo = as_userinfo(session, owner)
        ownerid = ownerinfo["id"]

    # load the buildinfo for all of the NVRs
    debug(f"Fed with {len(nvrs)} builds")

    # validate our list of NVRs first by attempting to load them
    loaded = bulk_load_builds(session, unique(nvrs), err=strict)

    # sort/dedup as requested
    if sorting == SORT_BY_NVR:
        debug("NVR sorting specified")
        builds = build_nvr_sort(loaded.values())
    elif sorting == SORT_BY_ID:
        debug("ID sorting specified")
        builds = build_id_sort(loaded.values())
    else:
        debug("No sorting specified, preserving feed order")
        builds = build_dedup(loaded.values())

    # at this point builds is a list of build info dicts
    if verbose:
        debug(f"Sorted and trimmed duplicates to {len(builds)} builds")
        for build in builds:
            debug(f" {build['nvr']} {build['id']}")

    if not builds:
        debug("Nothing to do!")
        return

    # check for missing package listings, and add as necessary
    if version_check(session, (1, 25)):
        # koji >= 1.25 allows us to not merge in package owner
        # data. Since we don't actually use that info, let's be kind
        # and avoid the join
        packages = session.listPackages(tagID=tagid,
                                        inherited=inherit,
                                        with_owners=False)
    else:
        packages = session.listPackages(tagID=tagid,
                                        inherited=inherit)

    package_ids = set(pkg["package_id"] for pkg in packages)

    package_todo = []

    for build in builds:
        pkgid = build["package_id"]
        if pkgid not in package_ids:
            package_ids.add(pkgid)
            package_todo.append((pkgid, ownerid or build["owner_id"]))

    if package_todo:
        # we've got some package listings that need adding

        debug("Beginning package additions")
        fn = lambda pad: session.packageListAdd(tagid, pad[0], owner=pad[1],
                                                force=force)

        for pad, res in iter_bulk_load(session, fn, package_todo, err=strict):
            # verify the results of our add-pkg calls. If strict was
            # set then the multicall would have raised an exception,
            # but we need to present any issues for the non-strict
            # cases as well
            if res and "faultCode" in res:
                printerr("Error adding package", pad[0],
                         ":", res["faultString"])

        debug("Package additions completed")

    # and finally, tag the builds themselves in chunks of 100
    debug("Begining build tagging")
    counter = 0
    for done in iter_bulk_tag_builds(session, taginfo, builds,
                                     force=force, notify=notify,
                                     size=100, strict=strict):

        for build, res in done:
            # same as with the add-pkg -- if strict was True then any
            # issues would raise an exception, but for non-strict
            # invocations we need to present the error messages
            if "faultCode" in res:
                printerr("Error tagging build", build["nvr"],
                         ":", res["faultString"])

        # and of course display the courtesy counter so the user
        # knows we're actually doing something
        counter += len(done)
        debug(f" tagged {counter}/{len(builds)}")

    debug("All done!")


class BulkTagBuilds(TagSmokyDingo):

    group = "bind"
    description = "Tag a large number of builds"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Tag to associate builds with")

        addarg("nvr", nargs="*", metavar="NVR",
               help="Build NVRs to tag")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        addarg("--create", action="store_true", default=False,
               help="Create the tag if it doesn't exist already")

        addarg("--strict", action="store_true", default=False,
               help="Stop processing at the first failure")

        addarg("--owner", action="store", default=None,
               help="Force missing package listings to be created"
               " with the specified owner")

        addarg("--no-inherit", action="store_false", default=True,
               dest="inherit", help="Do not use parent tags to"
               " determine existing package listing.")

        addarg("--force", action="store_true", default=False,
               help="Force tagging operations. Requires admin"
               " permission")

        addarg("--notify", action="store_true", default=False,
               help="Send tagging notifications. This can be"
               " expensive for koji hub, avoid unless absolutely"
               " necessary.")

        addarg("-v", "--verbose", action="store_true", default=False,
               help="Print tagging status")

        group = parser.add_argument_group("Tagging order of builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="pre-sort build list by NVR, so highest NVR is"
               " tagged last")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="pre-sort build list by build ID, so most recently"
               " completed build is tagged last")

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)

        if not nvrs and not sys.stdin.isatty():
            if not options.nvr_file:
                options.nvr_file = "-"

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        return cli_bulk_tag_builds(self.session, options.tag, nvrs,
                                   sorting=options.sorting,
                                   owner=options.owner,
                                   inherit=options.inherit,
                                   force=options.force,
                                   notify=options.notify,
                                   create=options.create,
                                   verbose=options.verbose,
                                   strict=options.strict)


def cli_bulk_untag_builds(
        session: ClientSession,
        tagname: TagSpec,
        nvrs: Sequence[Union[int, str]],
        force: bool = False,
        notify: bool = False,
        verbose: bool = False,
        strict: bool = False) -> None:

    """
    Implements the ``koji bulk-untag-builds`` command
    """

    # set up the verbose debugging output function
    if verbose:
        debug = printerr
    else:
        def debug(message):  # type: ignore
            pass

    taginfo = as_taginfo(session, tagname)

    # load the buildinfo for all of the NVRs
    debug(f"Fed with {len(nvrs)} builds")

    # validate our list of NVRs first by attempting to load them
    loaded = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = build_dedup(loaded.values())

    if verbose:
        debug(f"Trimmed duplicates to {len(builds)} builds")
        for build in builds:
            debug(f" {build['nvr']} {build['id']}")

    if not builds:
        debug("Nothing to do!")
        return

    # and finally, untag the builds themselves in chunks of 100
    debug("Begining build untagging")
    counter = 0
    for done in iter_bulk_untag_builds(session, taginfo, builds,
                                       force=force, notify=notify,
                                       size=100, strict=strict):

        for build, res in done:
            if "faultCode" in res:
                printerr("Error untagging build", build["nvr"],
                         ":", res["faultString"])

        # and of course display the courtesy counter so the user
        # knows we're actually doing something
        counter += len(done)
        debug(f" untagged {counter}/{len(builds)}")

    debug("All done!")


class BulkUntagBuilds(TagSmokyDingo):

    group = "bind"
    description = "Untag a large number of builds"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Tag to unassociate from builds")

        addarg("nvr", nargs="*", metavar="NVR",
               help="Build NVRs to untag")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        addarg("--strict", action="store_true", default=False,
               help="Stop processing at the first failure")

        addarg("--force", action="store_true", default=False,
               help="Force untagging operations. Requires admin"
               " permission")

        addarg("--notify", action="store_true", default=False,
               help="Send untagging notifications. This can be"
               " expensive for koji hub, avoid unless absolutely"
               " necessary.")

        addarg("-v", "--verbose", action="store_true", default=False,
               help="Print untagging status")

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)

        if not nvrs and not sys.stdin.isatty():
            if not options.nvr_file:
                options.nvr_file = "-"

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        return cli_bulk_untag_builds(self.session, options.tag, nvrs,
                                     force=options.force,
                                     notify=options.notify,
                                     verbose=options.verbose,
                                     strict=options.strict)


def cli_bulk_move_builds(
        session: ClientSession,
        srctag: TagSpec,
        desttag: str,
        nvrs: Sequence[Union[int, str]],
        sorting: Optional[str] = None,
        owner: Optional[Union[int, str]] = None,
        inherit: bool = False,
        force: bool = False,
        notify: bool = False,
        create: bool = False,
        verbose: bool = False,
        strict: bool = False) -> None:

    """
    Implements the ``koji bulk-move-builds`` command
    """

    # set up the verbose debugging output function
    if verbose:
        debug = printerr
    else:
        def debug(message):  # type: ignore
            pass

    # fetch the source tag info
    srctag = as_taginfo(session, srctag)

    # fetch the destination tag info (and make sure it actually
    # exists)
    dtag = ensure_tag(session, desttag) if create \
        else as_taginfo(session, desttag)
    tagid = dtag["id"]

    if srctag["id"] == tagid:
        debug("Source and destination tags are the same, nothing to do!")
        return

    # figure out how we're going to be dealing with builds that don't
    # have a matching pkg entry already. Someone needs to own them...
    ownerid = None
    if owner:
        ownerinfo = as_userinfo(session, owner)
        ownerid = ownerinfo["id"]

    # load the buildinfo for all of the NVRs
    debug(f"Fed with {len(nvrs)} builds")

    # validate our list of NVRs first by attempting to load them
    loaded = bulk_load_builds(session, unique(nvrs), err=strict)

    builds: List[BuildInfo]

    # sort/dedup as requested
    if sorting == SORT_BY_NVR:
        debug("NVR sorting specified")
        builds = build_nvr_sort(loaded.values())
    elif sorting == SORT_BY_ID:
        debug("ID sorting specified")
        builds = build_id_sort(loaded.values())
    else:
        debug("No sorting specified, preserving feed order")
        builds = build_dedup(loaded.values())

    # at this point builds is a list of build info dicts
    if verbose:
        debug(f"Sorted and trimmed duplicates to {len(builds)} builds")
        for build in builds:
            debug(f" {build['nvr']} {build['id']}")

    if not builds:
        debug("Nothing to do!")
        return

    # check for missing package listings, and add as necessary
    if version_check(session, (1, 25)):
        # koji >= 1.25 allows us to not merge in package owner
        # data. Since we don't actually use that info, let's be kind
        # and avoid the join
        packages = session.listPackages(tagID=tagid,
                                        inherited=inherit,
                                        with_owners=False)
    else:
        packages = session.listPackages(tagID=tagid,
                                        inherited=inherit)

    package_ids = set(pkg["package_id"] for pkg in packages)

    package_todo = []

    for build in builds:
        pkgid = build["package_id"]
        if pkgid not in package_ids:
            package_ids.add(pkgid)
            package_todo.append((pkgid, ownerid or build["owner_id"]))

    if package_todo:
        # we've got some package listings that need adding

        debug("Beginning package additions")
        fn = lambda pad: session.packageListAdd(tagid, pad[0], owner=pad[1],
                                                force=force)

        for pad, res in iter_bulk_load(session, fn, package_todo, err=strict):
            # verify the results of our add-pkg calls. If strict was
            # set then the multicall would have raised an exception,
            # but we need to present any issues for the non-strict
            # cases as well
            if res and "faultCode" in res:
                printerr("Error adding package", pad[0],
                         ":", res["faultString"])

        debug("Package additions completed")

    # and finally, move the builds themselves in chunks of 100
    debug("Begining build moving")
    counter = 0
    for done in iter_bulk_move_builds(session, srctag, dtag, builds,
                                      force=force, notify=notify,
                                      size=100, strict=strict):

        for build, res in done:
            # same as with the add-pkg -- if strict was True then any
            # issues would raise an exception, but for non-strict
            # invocations we need to present the error messages
            if res and "faultCode" in res:
                printerr("Error moving build", build["nvr"],
                         ":", res["faultString"])

        # and of course display the courtesy counter so the user
        # knows we're actually doing something
        counter += len(done)
        debug(f" moved {counter}/{len(builds)}")

    debug("All done!")


class BulkMoveBuilds(TagSmokyDingo):

    group = "bind"
    description = "Move a large number of builds between tags"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("srctag", action="store", metavar="SRCTAG",
               help="Tag to unassociate from builds")

        addarg("desttag", action="store", metavar="DESTTAG",
               help="Tag to associate with builds")

        addarg("nvr", nargs="*", metavar="NVR",
               help="Build NVRs to move")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        addarg("--create", action="store_true", default=False,
               help="Create the tag if it doesn't exist already")

        addarg("--strict", action="store_true", default=False,
               help="Stop processing at the first failure")

        addarg("--owner", action="store", default=None,
               help="Force missing package listings to be created"
               " with the specified owner")

        addarg("--no-inherit", action="store_false", default=True,
               dest="inherit", help="Do not use parent tags to"
               " determine existing package listing.")

        addarg("--force", action="store_true", default=False,
               help="Force tagging operations. Requires admin"
               " permission")

        addarg("--notify", action="store_true", default=False,
               help="Send tagging notifications. This can be"
               " expensive for koji hub, avoid unless absolutely"
               " necessary.")

        addarg("-v", "--verbose", action="store_true", default=False,
               help="Print tagging status")

        group = parser.add_argument_group("Tagging order of builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="pre-sort build list by NVR, so highest NVR is"
               " tagged last")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="pre-sort build list by build ID, so most recently"
               " completed build is tagged last")

        return parser


    def handle(self, options):

        nvrs = list(options.nvr)

        if not nvrs and not sys.stdin.isatty():
            if not options.nvr_file:
                options.nvr_file = "-"

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        return cli_bulk_move_builds(self.session,
                                    options.srctag, options.desttag, nvrs,
                                    sorting=options.sorting,
                                    owner=options.owner,
                                    inherit=options.inherit,
                                    force=options.force,
                                    notify=options.notify,
                                    create=options.create,
                                    verbose=options.verbose,
                                    strict=options.strict)


class BuildFiltering(BuildSifting):
    """
    Base class for commands which use build filtering options
    """

    def filtering_arguments(
            self,
            parser: ArgumentParser) -> ArgumentParser:

        grp = parser.add_argument_group("Filtering by tag")
        addarg = grp.add_argument

        addarg("--lookaside", action="append", default=list(),
               help="Omit builds found in this tag or its parent tags")

        addarg("--shallow-lookaside", action="append", default=list(),
               help="Omit builds found directly in this tag")

        addarg("--limit", action="append", default=list(),
               help="Limit results to builds found in this tag or its"
               " parent tags")

        addarg("--shallow-limit", action="append", default=list(),
               help="Limit results to builds found directly in this tag")

        grp = parser.add_argument_group("Filtering by type")
        addarg = grp.add_argument

        addarg("--type", action="append", dest="btypes",
               metavar="BUILD_TYPE", default=[],
               help="Limit to builds with this BType. May be specified"
               " multiple times to allow for more than one type.")

        addarg("--rpm", action="append_const", dest="btypes",
               const="rpm",
               help="Synonym for --type=rpm")

        addarg("--maven", action="append_const", dest="btypes",
               const="maven",
               help="Synonym for --type=maven")

        addarg("--image", action="append_const", dest="btypes",
               const="image",
               help="Synonym for --type=image")

        addarg("--win", action="append_const", dest="btypes",
               const="win",
               help="Synonym for --type=win")

        grp = parser.add_argument_group("Filtering by origin")
        addarg = grp.add_argument

        addarg("-c", "--content-generator", dest="cg_list",
               action="append", default=list(),
               metavar="CG_NAME",
               help="show content generator imports by build"
               " system name. Default: display no CG builds."
               " Specify 'any' to see CG imports from any system."
               " May be specified more than once.")

        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument
        addarg("--imports", action="store_true",
               dest="imported", default=None,
               help="Limit to imported builds")

        addarg("--no-imports", action="store_false",
               dest="imported", default=None,
               help="Invert the imports checking")

        grp = parser.add_argument_group("Filtering by state")
        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--completed",
               action="store_const", const=BuildState.COMPLETE,
               dest="state", default=None,
               help="Limit to completed builds")

        addarg("--deleted",
               action="store_const", const=BuildState.DELETED,
               dest="state", default=None,
               help="Limit to deleted builds")

        return parser


    def get_filter(
            self,
            session: ClientSession,
            options: Namespace) -> BuildFilter:
        # setup the limit as a set of IDs for each tag named in the
        # options.
        limit_ids = gather_tag_ids(session, deep=options.limit,
                                   shallow=options.shallow_limit)

        # setup the lookaside as a set of IDs for the tags in the
        # flattened inheritance of each tag named in the options.
        lookaside_ids = gather_tag_ids(session, deep=options.lookaside,
                                       shallow=options.shallow_lookaside)

        return BuildFilter(session,
                           limit_tag_ids=limit_ids,
                           lookaside_tag_ids=lookaside_ids,
                           imported=options.imported,
                           cg_list=options.cg_list,
                           btypes=options.btypes,
                           state=options.state)


def cli_list_components(
        session: ClientSession,
        nvr_list: Sequence[Union[int, str]],
        tags: Sequence[TagSpec] = (),
        inherit: bool = False,
        latest: bool = False,
        build_filter: Optional[BuildFilter] = None,
        build_sifter: Optional[Sifter] = None,
        sorting: Optional[str] = None,
        outputs: Optional[Dict[str, str]] = None) -> None:

    """
    Implements the ``koji list-component-builds`` command
    """

    nvr_list = unique(map(int_or_str, nvr_list))

    if nvr_list:
        # load the initial set of builds, validating them
        found = bulk_load_builds(session, nvr_list, err=True)
        loaded = {b["id"]: b for b in found.values()}

    else:
        loaded = {}

    for tag in tags:
        # mix in any tagged builds
        tag = as_taginfo(session, tag)
        tagged = session.listTagged(tag["id"], inherit=inherit, latest=latest)
        loaded.update((b["id"], b) for b in tagged)

    # the build IDs of all the builds we've loaded, combined from the
    # initial nvr_list, plus the builds from tag
    bids = list(loaded)

    # now that we have bids (the build IDs to gather components from)
    # we can begin the real work.
    components = gather_component_build_ids(session, bids)

    # now we need to turn those components build IDs into build_infos
    component_ids = unique(chain(*components.values()))
    found = bulk_load_builds(session, component_ids)

    # we'll also want the underlying builds used to produce any
    # standalone wrapperRPM builds, as those are not recorded as
    # normal buildroot components
    tids = [b["task_id"] for b in loaded.values() if b["task_id"]]
    wrapped = gather_wrapped_builds(session, tids)

    builds = list(found.values())
    builds.extend(wrapped.values())

    if build_filter:
        builds = list(build_filter(builds))

    if build_sifter:
        results = build_sifter(session, builds)
    else:
        results = {"default": builds}

    sortfn: Callable
    if sorting == SORT_BY_NVR:
        sortfn = build_nvr_sort
    elif sorting == SORT_BY_ID:
        sortfn = build_id_sort
    elif not build_sifter:
        sortfn = build_dedup
    else:
        sortfn = None

    output_sifted(results, "nvr", outputs, sort=sortfn)  # type: ignore


class ListComponents(AnonSmokyDingo, BuildFiltering):

    description = "List a build's component dependencies"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("nvr", nargs="*", type=int_or_str, metavar="NVR",
               help="Build NVRs to list components of")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        group = parser.add_argument_group("Components of tagged builds")
        addarg = group.add_argument

        addarg("--tag", action="append", default=[],
               metavar="TAG", dest="tags",
               help="Look for components of builds in this tag")

        addarg("--inherit", action="store_true", default=False,
               help="Follow inheritance")

        addarg("--latest", action="store_true", default=False,
               help="Limit to latest builds")

        group = parser.add_argument_group("Sorting of builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="Sort output by NVR in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Build ID in ascending order")

        # additional build filtering arguments
        parser = self.filtering_arguments(parser)
        parser = self.sifter_arguments(parser)

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)
        tags = resplit(options.tags)

        if not (nvrs or sys.stdin.isatty()):
            if not options.nvr_file:
                options.nvr_file = "-"

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        bf = self.get_filter(self.session, options)
        bs = self.get_sifter(options)
        sorting = options.sorting
        outputs = self.get_outputs(options)

        return cli_list_components(self.session, nvrs,
                                   tags=tags,
                                   inherit=options.inherit,
                                   latest=options.latest,
                                   build_filter=bf,
                                   build_sifter=bs,
                                   sorting=sorting,
                                   outputs=outputs)


def cli_filter_builds(
        session: ClientSession,
        nvr_list: Iterable[Union[int, str]],
        tags: Iterable[TagSpec] = (),
        inherit: bool = False,
        latest: bool = False,
        build_filter: Optional[BuildFilter] = None,
        build_sifter: Optional[Sifter] = None,
        sorting: Optional[str] = None,
        outputs: Optional[Dict[str, str]] = None,
        strict: bool = False) -> None:

    """
    Implements the ``koji filter-builds`` command
    """

    nvr_list = unique(map(int_or_str, nvr_list))

    builds: Iterable[BuildInfo]
    if nvr_list:
        loaded = bulk_load_builds(session, nvr_list, err=strict)
        builds = filter(None, loaded.values())
    else:
        builds = ()

    for tag in tags:
        taginfo = as_taginfo(session, tag)
        listTagged = partial(session.listTagged, taginfo["id"],
                             inherit=inherit, latest=latest)

        # server-side optimization if we're doing filtering by btype
        if build_filter and build_filter._btypes:
            tagged = []
            for btype in build_filter._btypes:
                tagged.extend(listTagged(type=btype))
        else:
            tagged = listTagged()

        if tagged:
            builds = list(builds)
            known_ids = set(b["id"] for b in builds)
            tagged_ids = set(b["id"] for b in tagged)
            loaded = bulk_load_builds(session, tagged_ids - known_ids)
            if loaded:
                builds.extend(loaded.values())

    if build_filter:
        builds = build_filter(builds)

    if build_sifter:
        results = build_sifter(session, builds)
    else:
        results = {"default": list(builds)}

    sortfn: Callable
    if sorting == SORT_BY_NVR:
        sortfn = build_nvr_sort
    elif sorting == SORT_BY_ID:
        sortfn = build_id_sort
    elif not build_sifter:
        sortfn = build_dedup
    else:
        sortfn = None

    output_sifted(results, "nvr", outputs, sort=sortfn)  # type: ignore


class FilterBuilds(AnonSmokyDingo, BuildFiltering):

    description = "Filter a list of NVRs by various criteria"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("nvr", nargs="*", metavar="NVR")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        addarg("--strict", action="store_true", default=False,
               help="Error if any of the NVRs do not resolve into a"
               " real build. Otherwise, bad NVRs are ignored.")

        group = parser.add_argument_group("Working from tagged builds")
        addarg = group.add_argument

        addarg("--tag", action="append", default=[],
               metavar="TAG", dest="tags",
               help="Filter using the builds in this tag")

        addarg("--inherit", action="store_true", default=False,
               help="Follow inheritance")

        addarg("--latest", action="store_true", default=False,
               help="Limit to latest builds")

        group = parser.add_argument_group("Sorting of output builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="Sort output by NVR in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Build ID in ascending order")

        # additional build filtering arguments
        parser = self.filtering_arguments(parser)
        parser = self.sifter_arguments(parser)

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)
        tags = resplit(options.tags)

        if not (nvrs or sys.stdin.isatty()):
            if not options.nvr_file:
                options.nvr_file = "-"

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        bf = self.get_filter(self.session, options)
        bs = self.get_sifter(options)
        sorting = options.sorting
        outputs = self.get_outputs(options)

        return cli_filter_builds(self.session, nvrs,
                                 tags=tags,
                                 inherit=options.inherit,
                                 latest=options.latest,
                                 build_filter=bf,
                                 build_sifter=bs,
                                 sorting=sorting,
                                 outputs=outputs,
                                 strict=options.strict)


def cli_list_btypes(
        session: ClientSession,
        nvr: Optional[BuildSpec] = None,
        json: bool = False,
        quiet: bool = False) -> None:
    """
    Implements ``koji list-btypes`` command
    """

    btypes_ids: Dict[int, BTypeInfo]
    btypes_ids = {bt["id"]: bt for bt in session.listBTypes()}

    if nvr:
        build = as_buildinfo(session, nvr)
        dbuild = decorate_builds_btypes(session, [build])[0]
        build_bts = dbuild["archive_btype_ids"]

        for btid in list(btypes_ids):
            if btid not in build_bts:
                btypes_ids.pop(btid)

    btypes: List[BTypeInfo]
    btypes = sorted(btypes_ids.values(), key=itemgetter("id"))

    if json:
        pretty_json(btypes)
        return

    if quiet:
        fmt = "{name}".format

    else:
        fmt = "  {name} [{id}]".format
        if nvr:
            print(f"Build Types for {build['nvr']} [{build['id']}]")
        else:
            print("Build Types")

    for bt in btypes:
        print(fmt(**bt))


class ListBTypes(AnonSmokyDingo):
    """
    Koji client command 'list-btypes'
    """

    description = "List BTypes"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("--build", action="store", default=None,
               metavar="NVR", help="List the BTypes in a given build")

        addarg("--json", action="store_true", default=False,
               help="Output as JSON")

        addarg("--quiet", "-q", action="store_true", default=False,
               help="Output just the BType names")

        return parser


    def handle(self, options):
        return cli_list_btypes(self.session,
                               nvr=options.build,
                               json=options.json,
                               quiet=options.quiet)


def cli_list_cgs(
        session: ClientSession,
        nvr: Optional[BuildSpec] = None,
        json: bool = False,
        quiet: bool = False) -> None:
    """
    Implements the ``koji list-cgs`` command
    """

    cgs = {cg['id']: cg for cg in collect_cgs(session)}

    if nvr:
        build = as_buildinfo(session, nvr)
        dbuild = decorate_builds_cg_list(session, [build])[0]
        build_cgs = dbuild["archive_cg_ids"]

        for cgid in cgs:
            if cgid not in build_cgs:
                cgs.pop(cgid)

    keep_cgs = sorted(cgs.values(), key=itemgetter("id"))

    if json:
        pretty_json(keep_cgs)
        return

    if quiet:
        fmt = "{name}".format

    else:
        fmt = "  {name} [{id}]".format
        if nvr:
            print(f"Content Generators for {build['nvr']} [{build['id']}]")
        else:
            print("Content Generators")

    for cg in keep_cgs:
        print(fmt(**cg))


class ListCGs(AnonSmokyDingo):

    description = "List Content Generators"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("--build", action="store", default=None,
               metavar="NVR", help="List the Content Generators"
               " used to produce a given build")

        addarg("--json", action="store_true", default=False,
               help="Output as JSON")

        addarg("--quiet", "-q", action="store_true", default=False,
               help="Output just the CG names")

        return parser


    def handle(self, options):
        return cli_list_cgs(self.session,
                            nvr=options.build,
                            json=options.json,
                            quiet=options.quiet)


def cli_pull_container(
        session: ClientSession,
        goptions: GOptions,
        cmd: str,
        tagcmd: str,
        bld: str,
        tag: Optional[TagSpec] = None) -> int:

    """
    Implements the ``koji pull-container`` command
    """

    if tag:
        tinfo = as_taginfo(session, tag)
        latest = session.getLatestBuilds(tinfo['id'], package=bld)
        if not latest:
            raise BadDingo(f"No latest build of {bld} in {tag}")
        binfo = as_buildinfo(session, latest[0]['build_id'])

    else:
        binfo = as_buildinfo(session, bld)

    pull: List[str] = None
    extra: Dict[str, Any] = binfo.get("extra")
    if extra:
        image: Dict[str, Any] = extra.get("image")
        if image:
            index: Dict[str, Any] = image.get("index")
            if index:
                pull = index.get("pull")

    if not pull:
        raise BadDingo("Unable to determine pull spec from extra data")

    for pullspec in pull:
        if "@sha" not in pullspec:
            break

    if not cmd or cmd == "-":
        print(pullspec)
        return 0

    pullspec = quote(pullspec)
    if "{pullspec}" in cmd:
        cmd = cmd.format(pullspec=pullspec)
    else:
        cmd = f'{cmd} {pullspec}'

    # bandit complains about this -- we've quoted our args, and the
    # invocation has the same level of authority as the user running
    # the command. They could do something drastic if they wanted to,
    # just like they could do something drastic from the shell they
    # already have access to. This tool isn't a service.
    print(cmd)
    res = system(cmd)  # nosec
    if res:
        return res

    if not tagcmd or tagcmd == "-":
        return 0

    profile = quote(goptions.profile)
    nvr = quote(binfo['nvr'])
    if "{" in tagcmd:
        tagcmd = tagcmd.format(pullspec=pullspec,
                               profile=profile, nvr=nvr)
    else:
        tagcmd = f'{tagcmd} {pullspec} {profile}/{nvr}'

    print(tagcmd)
    return system(tagcmd)  # nosec


class PullContainer(AnonSmokyDingo):

    description = "Pull a container build's image"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("build", metavar="BUILD", action="store",
               help="Container build to pull")

        addarg("--latest-build", dest="kojitag", metavar="KOJI_TAG",
               action="store", default=None,
               help="BUILD is a package name, use the matching latest build"
               " in the given koji tag")

        grp = parser.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--command", default=None, metavar="PULL_COMMAND",
               help="Command to exec with the discovered pull spec")

        addarg("--print", "-p", default=None, dest="command",
               action="store_const", const="-",
               help="Print pull spec to stdout rather than executing"
               " a command")

        grp = parser.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--tag-command", dest="tag_command", default=None,
               metavar="TAG_COMMAND",
               help="Command to exec after pulling the image")

        addarg("--no-tag", "-n", dest="tag_command",
               action="store_const", const="-",
               help="Do not execute the tag command after pulling the"
               " image")

        return parser


    def validate(self, parser, options):
        command = options.command

        if not command:
            command = self.get_plugin_config("pull_command",
                                             "podman pull")
            options.command = command

        if not command:
            parser.error("Unable to determine a default COMMAND for"
                         " pulling containers.\n"
                         "Please specify via the '--command' option.")

        tag_command = options.tag_command
        if not tag_command:
            tag_command = self.get_plugin_config("tag_command",
                                                 "podman image tag")
            options.tag_command = tag_command

        # don't bother warning about the lack of a tag_command, that
        # part can just be skipped.


    def handle(self, options):
        return cli_pull_container(self.session,
                                  goptions=self.goptions,
                                  cmd=options.command,
                                  tagcmd=options.tag_command,
                                  bld=options.build,
                                  tag=options.kojitag)


#
# The end.
