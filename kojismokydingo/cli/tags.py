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

from six.moves import zip

from . import AnonSmokyDingo, TagSmokyDingo, printerr
from .. import BadDingo, NoSuchTag
from ..tags import get_affected_targets, renum_inheritance, find_inheritance


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


def cli_renum_tag(session, tagname, begin=10, step=10,
                  verbose=False, test=False):

    if not session.getTag(tagname):
        raise NoSuchTag(tagname)

    original = session.getInheritanceData(tagname)
    renumbered = renum_inheritance(original, begin, step)

    if test or verbose:
        print("Renumbering inheritance priorities for", tagname)
        for left, right in zip(original, renumbered):
            name = left['name']
            lp = left['priority']
            rp = right['priority']
            print(" %3i -> %3i  %s" % (lp, rp, name))

    if test:
        print("Changes not committed in test mode.")

    else:
        results = session.setInheritanceData(tagname, renumbered)
        if verbose and results:
            print(results)


class RenumTagInheritance(TagSmokyDingo):

    description = "Renumbers inheritance priorities of a tag," \
                  " preserving order"


    def parser(self):
        argp = super(RenumTagInheritance, self).parser()
        addarg = argp.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Tag to renumber")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Print information about what's changing")

        addarg("--test", "-t", action="store_true", default=False,
               help="Calculate the new priorities, but don't commit"
               " the changes")

        addarg("--begin", "-b", action="store", type=int, default=10,
               help="New priority for first inheritance link"
               " (default: 10)")

        addarg("--step", "-s", action="store", type=int, default=10,
               help="Priority increment for each subsequent"
               " inheritance link after the first (default: 10)")

        return argp


    def validate(self, parser, options):
        begin = options.begin
        if begin < 0:
            parser.error("begin value must not be negative")

        elif begin >= 1000:
            parser.error("don't be ridiculous")

        step = options.step
        if step < 1:
            parser.error("priority increment must be positive"
                         " (no reversing)")

        elif step > 100:
            parser.error("don't be ridiculous")


    def handle(self, options):
        return cli_renum_tag(self.session, options.tag,
                             options.begin, options.step,
                             options.verbose, options.test)


class BadSwap(BadDingo):
    complaint = "Wonky inheritance swap requested"


class NoSuchInheritance(BadDingo):
    complaint = "No such inheritance link"


def cli_swap_inheritance(session, tagname, old_parent, new_parent,
                         verbose=False, test=False):

    if tagname in (old_parent, new_parent) or old_parent == new_parent:
        raise BadSwap(tagname, old_parent, new_parent)

    original = session.getInheritanceData(tagname)
    if original is None:
        raise NoSuchTag(tagname)

    old_p = session.getTag(old_parent)
    if old_p is None:
        raise NoSuchTag(old_parent)

    new_p = session.getTag(new_parent)
    if new_p is None:
        raise NoSuchTag(new_parent)

    # deep copy of original inheritance
    swapped = [dict(i) for i in original]

    found_old = find_inheritance(swapped, old_p["id"])
    found_new = find_inheritance(swapped, new_p["id"])

    if found_old is None:
        raise NoSuchInheritance(tagname, old_parent)

    # this looks convoluted, because we're doing two things at
    # once. First, we're duplicating the whole inheritance structure
    # so we can show what's changed. Second, we're collecting the
    # changes as either two edits, or a delete and an addition.

    if found_new is None:
        # the new inheritance isn't in the current inheritance
        # structure, therefore duplicate the old inheritance link and
        # mark it as a deletion, and then modify the old inheritance
        # link later.
        changed_old = dict(found_old)
        changed_old['delete link'] = True
        changes = [changed_old, found_old]

    else:
        # the new inheritance link is also within the current
        # inheritance structure, therefore this is an action to make
        # two edits. Mix in the updated new inheritance data now, and
        # the old inheritance link will be updated at the end.
        changes = [found_old, found_new]
        found_new["name"] = old_p["name"]
        found_new["parent_id"] = old_p["id"]

    # we do this last so that we'll have a chance to duplicate the
    # original if needed
    found_old["name"] = new_p["name"]
    found_old["parent_id"] = new_p["id"]

    # at this point the swapped list represents the fully modified
    # inheritance structure we'd like to see, and changes represents
    # just the two edits we're making.

    if test or verbose:
        print("Swapping inheritance data for", tagname)
        for left, right in zip(original, swapped):
            priority = left['priority']
            lp = left['name']
            rp = right['name']
            if lp != rp:
                print(" %3i: %s -> %s" % (priority, lp, rp))
            else:
                print(" %3i: %s" % (priority, lp))

    if test:
        print("Changes not committed in test mode.")
    else:
        results = session.setInheritanceData(tagname, changes)
        if verbose and results:
            print(results)


class SwapTagInheritance(TagSmokyDingo):

    description = "Swap a tag's inheritance"


    def parser(self):
        """
        Swaps TAG's inheritance from OLD_PARENT to NEW_PARENT, preserving
        priority. If NEW_PARENT was already in the inheritance of TAG,
        OLD_PARENT will be put in its place, effectively exchanging
        the two parent priorities.
        """

        parser = super(SwapTagInheritance, self).parser()
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag to modify")

        addarg("old_parent", action="store", metavar="OLD_PARENT_TAG",
               help="Old parent tag's name")

        addarg("new_parent", action="store", metavar="NEW_PARENT_TAG",
               help="New parent tag's name")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Print information about what's changing")

        addarg("--test", "-t", action="store_true", default=False,
               help="Calculate the new inheritance, but don't commit"
               " the changes.")

        return parser


    def handle(self, options):
        return cli_swap_inheritance(self.session, options.tag,
                                    options.old_parent, options.new_parent,
                                    options.verbose, options.test)


#
# The end.
