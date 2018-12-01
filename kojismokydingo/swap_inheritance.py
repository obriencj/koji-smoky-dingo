# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


"""
Koji Smoky Dingo - admin command swap-inheritance

Swaps inheritance between two parent tags in a brew tag.

If only the original tag is already present in the inheritance, it
will be switched for its replacement.

If both the original and the replacement are in the inheritance, they
will have their priorities swapped.

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys

from six.moves import zip as izip

from . import AdminSmokyDingo, BadDingo, NoSuchTag


class BadSwap(BadDingo):
    complaint = "Wonky inheritance swap requested"


class NoSuchInheritance(BadDingo):
    complaint = "No such inheritance link"


def find_inheritance(inheritance, parent_id):
    for i in inheritance:
        if i["parent_id"] == parent_id:
            return i
    else:
        return None


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
    else:
        found_old["name"] = new_p["name"]
        found_old["parent_id"] = new_p["id"]

    if found_new is not None:
        # perform the optional behavior if both new and old are
        # parents, and effectively swap their priorities.

        found_new["name"] = old_p["name"]
        found_new["parent_id"] = old_p["id"]

    if test or verbose:
        print("Swapping inheritance data for", tagname)
        for left, right in izip(original, swapped):
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
        results = brewhub.setInheritanceData(tagname, swapped, clear=True)
        if verbose and results:
            print(results)


class cli(AdminSmokyDingo):

    description = "Swap a tag's inheritance"


    def parser(self):
        """
        Swaps TAG's inheritance from OLD_PARENT to NEW_PARENT, preserving
        priority. If NEW_PARENT was already in the inheritance of TAG,
        OLD_PARENT will be put in its place, effectively exchanging
        the two parent priorities.
        """

        parser = super(cli, self).parser()
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag to modify")

        addarg("old_parent", action="store", metavar="OLD_PARENT_TAG",
               help="Old parent tag's name")

        addarg("new_parent", action="store", metavar="NEW_PARENT_TAG",
               help="New parent tag's name")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Print information about what's changing")

        addarg("--test", "-t", action="store_true",  default=False,
               help="Calculate the new inheritance, but don't commit"
               " the changes.")

        return parser


    def handle(self, options):
        return cli_swap_inheritance(options.session, options.tagname,
                                    options.old_parent, options.new_parent,
                                    options.verbose, options.test)


#
# The end.
