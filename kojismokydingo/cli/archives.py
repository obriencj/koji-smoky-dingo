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


from __future__ import print_function

from . import AnonSmokyDingo, pretty_json, resplit
from .. import NoSuchBuild
from ..archives import \
    filter_archives, gather_build_archives, gather_latest_archives


def cli_list_build_archives(session, nvr, btype,
                            atypes=(), rpmkeys=(),
                            path=None, json=False):

    # quick sanity check, and we'll work with the build info rather
    # than the NVR from here on out
    binfo = session.getBuild(nvr)
    if not binfo:
        raise NoSuchBuild(nvr)

    found = gather_build_archives(session, binfo, btype,
                                  rpmkeys, path)

    if atypes:
        found = filter_archives(session, found, atypes)

    if json:
        pretty_json(found)

    else:
        for f in found:
            print(f["filepath"])


def cli_latest_tag_archives(session, tagname, btype,
                            atypes=(), rpmkeys=(),
                            inherit=True, path=None,
                            json=False):

    found = gather_latest_archives(session, tagname, btype,
                                   rpmkeys, inherit, path)

    if atypes:
        found = filter_archives(session, found, atypes)

    if json:
        pretty_json(found)

    else:
        for f in found:
            print(f["filepath"])


class ArchiveDingo(AnonSmokyDingo):

    group = "info"


    def archive_arguments(self, parser):
        goptions = self.goptions

        addarg = parser.add_argument
        addarg("--json", action="store_true", default=False,
               help="Output archive information as JSON")

        addarg("--urls", "-U", action="store_const",
               dest="path", const=goptions.topurl, default=goptions.topdir,
               help="Present archives as URLs using the configured topurl."
               " Default: use the configured topdir")

        grp = parser.add_argument_group("Build Filtering Options")
        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--build-type", action="store", metavar="TYPE",
               dest="btype", default=None,
               help="Only show archives for the given build type. Example"
               " types are rpm, maven, image, win. Default: show all"
               " archives.")

        addarg("--rpm", action="store_const", dest="btype",
               const="rpm",
               help="--build-type=rpm")

        addarg("--maven", action="store_const", dest="btype",
               const="maven",
               help="--build-type=maven")

        addarg("--image", action="store_const", dest="btype",
               const="image",
               help="--build-type=image")

        addarg("--win", action="store_const", dest="btype",
               const="win",
               help="--build-type=win")

        grp = parser.add_argument_group("Archive Filtering Options")
        addarg = grp.add_argument

        addarg("--archive-type", "-a", action="append", metavar="EXT",
               dest="atypes", default=[],
               help="Only show archives with the given archive type."
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


    def validate(self, parser, options):
        options.atypes = resplit(options.atypes)

        keys = resplit(options.keys)
        if keys and options.unsigned:
            keys.append('')
        options.keys = keys


class ListBuildArchives(ArchiveDingo):

    description = "List archives from a build"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("nvr", metavar="NVR",
               help="The NVR containing the archives")

        parser = self.archive_arguments(parser)
        return parser


    def handle(self, options):
        return cli_list_build_archives(self.session, options.nvr,
                                       btype=options.btype,
                                       atypes=options.atypes,
                                       rpmkeys=options.keys,
                                       path=options.path,
                                       json=options.json)


class LatestArchives(ArchiveDingo):

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


    def handle(self, options):
        return cli_latest_tag_archives(self.session, options.tag,
                                       btype=options.btype,
                                       atypes=options.atypes,
                                       rpmkeys=options.keys,
                                       inherit=options.inherit,
                                       path=options.path,
                                       json=options.json)


#
# The end.
