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

from itertools import chain

from . import AnonSmokyDingo, NoSuchTag, printerr


def get_affected_targets(session, tagname_list):

    tags = list()
    for tname in set(tagname_list):
        tag = session.getTag(tname)
        if not tag:
            raise NoSuchTag(tname)
        else:
            tags.append(tag)

    session.multicall = True
    for tag in tags:
        session.getFullInheritance(tag['id'], reverse=True)
    parents = [p[0] for p in session.multiCall() if p]

    tagids = set(chain(*((ch['tag_id'] for ch in ti) for ti in parents)))
    tagids.update(tag['id'] for tag in tags)

    session.multicall = True
    for ti in tagids:
        session.getBuildTargets(buildTagID=ti)

    return list(chain(*(t[0] for t in session.multiCall() if t)))


def cli_affected_targets(session, tag_list,
                         build_tags=False, info=False,
                         quiet=False):

    targets = get_affected_targets(session, tag_list)

    debug = printerr if not quiet else lambda *m: None

    if info:
        # convert the targets into info tuples
        infos = sorted((t['name'], t['build_tag_name'], t['dest_tag_name'])
                       for t in targets)
        output = [" ".join(t) for t in infos]

    else:
        # get a unique sorted list of either the target names or the
        # build tag names for the targets
        attr = 'build_tag_name' if build_tags else 'name'
        output = sorted(set(targ[attr] for targ in targets))

    if build_tags:
        debug("Found %i affected build tags inheriting:" % len(output))
    else:
        debug("Found %i affected targets inheriting:" % len(output))

    # for debugging we re-print the tags we operated on
    for tag in sorted(set(tag_list)):
        debug(" ", tag)

    if output:
        debug('-' * 40)
        for o in output:
            print(o)


class AffectedTargets(AnonSmokyDingo):

    description = "Show targets impacted by changes to the given tag(s)"


    def parser(self):
        argp = super(AffectedTargets, self).parser()
        addarg = argp.add_argument

        addarg("tags", nargs="+", metavar="TAGNAME",
               help="Tag to check")

        addarg("-q", "--quiet", action="store_true", default=False,
               help="Don't print summary information")

        group = argp.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("-i", "--info", action="store_true", default=False,
               help="Print target name, build tag name, dest tag name")

        addarg("-b", "--build-tags", action="store_true", default=False,
               help="Print build tag names rather than target names")

        return argp


    def handle(self, options):
        return cli_affected_targets(self.session, options.tags,
                                    options.build_tags, options.info,
                                    options.quiet)


#
# The end.
