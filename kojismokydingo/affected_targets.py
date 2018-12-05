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
Koji Smoky Dingo - info command affected-targets

Given a tag (or tags) display all of the targets that will be affected
if the tag changes.

In other words, look through the reversed inheritance of the tag, and
collect any targets on each child.

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys
from functools import partial
from itertools import chain

from . import SmokyDingo, NoSuchTag


def cli_affected_targets(session, tag_list,
                         build_tags=False, info=False,
                         quiet=False):

    if quiet:
        debug = partial(print, file=sys.stderr)
    else:
        def debug(*m):
            pass

    tags = list()
    for tname in tag_list:
        tag = session.getTag(tname)
        if not tag:
            raise NoSuchTag(tname)
        else:
            tags.append(tag)

    session.multicall = True
    for tag in tags:
        session.getFullInheritance(tag['id'], reverse=True)
    parents = session.multiCall()

    session.multicall = True
    for ti in parents:
        for child in ti:
            session.getBuildTargets(buildTagID=child['tag_id'])
    targets = chain(*session.multiCall())

    if info:
        targets = ((t['name'], t['build_tag_name'], t['dest_tag_name'])
                   for t in targets)
        output = [" ".join(t) for t in sorted(targets)]

    else:
        attr = 'build_tag_name' if build_tags else 'name'
        output = sorted(set(targ[attr] for targ in targets))

    if build_tags:
        debug("Found %i affected build tags inheriting:" % len(output))
    else:
        debug("Found %i affected targets inheriting:" % len(output))

    for tag in sorted(set(tag['name'] for tag in tags)):
        debug(" ", tag)

    if output:
        debug('-' * 40)
        for o in output:
            print(o)


class cli(SmokyDingo):

    description = "Show targets impacted by changes to the given tag(s)"


    def parser(self):
        parser = super(SmokyDingo, self).parser()
        addarg = parser.add_argument

        addarg("tags", nargs="+", metavar="TAGNAME",
               help="Tag to check")

        addarg("-q", "--quiet", action="store_true", default=False,
               help="Don't print summary information")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("-i", "--info", action="store_true", default=False,
               help="Print target name, build tag name, dest tag name")

        addarg("-b", "--build-tags", action="store_true", default=False,
               help="Print build tag names rather than target names")

        return parser


    def handle(self, options):
        return cli_affected_targets(options.session, options.tags,
                                    options.build_tags, options.info,
                                    options.quiet)


#
# The end.
