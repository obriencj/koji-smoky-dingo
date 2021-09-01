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
Koji Smoky Dingo - CLI Archive and RPM Commands

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from argparse import SUPPRESS, ArgumentParser, Namespace
from koji import ClientSession
from typing import Iterable, List, Optional, Sequence, Union, cast

from . import AnonSmokyDingo, pretty_json, resplit
from .. import bulk_load_builds
from ..archives import (
    filter_archives, gather_build_archives, gather_latest_archives, )
from ..builds import build_dedup
from ..types import (
    BuildState, PathSpec, )


__all__ = (
    "ArchiveFiltering",
    "LatestArchives",
    "ListBuildArchives",

    "cli_latest_tag_archives",
    "cli_list_build_archives",
)


def cli_list_build_archives(
        session: ClientSession,
        nvrs: Iterable[Union[int, str]],
        btype: Optional[str] = None,
        atypes: Sequence[str] = (),
        arches: Sequence[str] = (),
        rpmkeys: Sequence[str] = (),
        deleted: bool = False,
        path: Optional[PathSpec] = None,
        json: bool = False):
    """
    Implements the ``koji list-build-archives`` command
    """

    loaded = bulk_load_builds(session, nvrs)
    found = []

    for binfo in build_dedup(loaded.values()):
        # the meaning of the --show-deleted/-d setting is a little
        # different than explained. Any non-COMPLETE build will
        # normally show no archives, but with that setting enabled,
        # any state will show archives if the data is recorded in
        # koji.
        if deleted or binfo.get("state") == BuildState.COMPLETE:
            found.extend(gather_build_archives(session, binfo, btype,
                                               rpmkeys, path))

    filtered = filter_archives(session, found, atypes, arches)

    if json:
        pretty_json(tuple(filtered))
        return

    for f in filtered:
        print(f["filepath"])


def cli_latest_tag_archives(
        session: ClientSession,
        tagname: str,
        btype: Optional[str] = None,
        atypes: Sequence[str] = (),
        arches: Sequence[str] = (),
        rpmkeys: Sequence[str] = (),
        inherit: bool = True,
        path: Optional[PathSpec] = None,
        json: bool = False):
    """
    Implements the ``koji latest-archives`` command
    """

    found = gather_latest_archives(session, tagname, btype,
                                   rpmkeys, inherit, path)

    filtered = filter_archives(session, found, atypes, arches)

    if json:
        pretty_json(tuple(filtered))
        return

    for f in filtered:
        print(f["filepath"])


class ArchiveFiltering():
    """ Mixin for SmokyDingos which need archive-filtering arguments """

    def archive_arguments(
            self,
            parser: ArgumentParser) -> ArgumentParser:

        addarg = parser.add_argument
        addarg("--json", action="store_true", default=False,
               help="Output archive information as JSON")

        addarg("--urls", "-U", action="store_true",
               dest="as_url",
               help="Present archives as URLs using the configured topurl."
               " Default: use the configured topdir")

        grp = parser.add_argument_group("Build Filtering Options")
        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--build-type", action="store", metavar="TYPE",
               dest="btype", default=None,
               help=SUPPRESS)

        addarg("--type", action="store", metavar="TYPE",
               dest="btype", default=None,
               help="Only show archives for the given build type. Example"
               " types are rpm, maven, image, win. Default: show all"
               " archives.")

        addarg("--rpm", action="store_const", dest="btype",
               const="rpm",
               help="Synonym for --type=rpm")

        addarg("--maven", action="store_const", dest="btype",
               const="maven",
               help="Synonym for --type=maven")

        addarg("--image", action="store_const", dest="btype",
               const="image",
               help="Synonym for --type=image")

        addarg("--win", action="store_const", dest="btype",
               const="win",
               help="Synonym for --type=win")

        grp = parser.add_argument_group("Archive Filtering Options")
        addarg = grp.add_argument

        addarg("--archive-type", action="append", metavar="EXT",
               dest="atypes", default=[],
               help="Only show archives with the given archive type."
               " Can be specified multiple times. Default: show all")

        addarg("--arch", action="append",
               dest="arches", default=[],
               help="Only show archives with the given arch."
               " Can be specified multiple times. Default: show all")

        grp = parser.add_argument_group("RPM Options")
        addarg = grp.add_argument

        addarg("--key", "-k", dest="keys", metavar="KEY",
               action="append", default=[],
               help="Only show RPMs signed with the given key. Can be"
               " specified multiple times to indicate any of the keys is"
               " valid. Preferrence is in order defined. Default: show"
               " unsigned RPMs")

        addarg("--unsigned", action="store_true",
               help="Allow unsigned copies if no signed copies are"
               " found when --key=KEY is specified. Otherwise if keys are"
               " specified, then only RPMs signed with one of those keys"
               " are shown.")

        return parser


    def validate_archive_options(
            self,
            parser: ArgumentParser,
            options: Namespace) -> None:

        options.atypes = resplit(options.atypes)
        options.arches = resplit(options.arches)

        keys = resplit(options.keys)
        if keys and options.unsigned:
            keys.append('')
        options.keys = keys


class ListBuildArchives(AnonSmokyDingo, ArchiveFiltering):

    description = "List archives from a build"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("nvrs", nargs="+", metavar="NVR",
               help="The NVR containing the archives")

        addarg("--show-deleted", "-d", dest="deleted",
               action="store_true", default=False,
               help="Show archives for a deleted build. Default, deleted"
               " builds show an empty archive list")

        parser = self.archive_arguments(parser)
        return parser


    def validate(self, parser, options):

        goptions = self.goptions
        if options.as_url:
            options.path = goptions.topurl
        else:
            options.path = goptions.topdir

        return self.validate_archive_options(parser, options)


    def handle(self, options):
        return cli_list_build_archives(self.session, options.nvrs,
                                       btype=options.btype,
                                       atypes=options.atypes,
                                       arches=options.arches,
                                       rpmkeys=options.keys,
                                       deleted=options.deleted,
                                       path=options.path,
                                       json=options.json)


class LatestArchives(AnonSmokyDingo, ArchiveFiltering):

    description = "List latest archives from a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", metavar="TAGNAME",
               help="The tag containing the archives")

        addarg("--noinherit", action="store_false",
               dest="inherit", default=True,
               help="Do not follow inheritance")

        parser = self.archive_arguments(parser)
        return parser


    def validate(self, parser, options):

        goptions = self.goptions
        if options.as_url:
            options.path = goptions.topurl
        else:
            options.path = goptions.topdir

        return self.validate_archive_options(parser, options)


    def handle(self, options):
        return cli_latest_tag_archives(self.session, options.tag,
                                       btype=options.btype,
                                       atypes=options.atypes,
                                       arches=options.arches,
                                       rpmkeys=options.keys,
                                       inherit=options.inherit,
                                       path=options.path,
                                       json=options.json)


#
# The end.
