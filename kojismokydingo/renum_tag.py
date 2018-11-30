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
Koji Smoky Dingo - admin command renum-tag

Remember RENUM from BASIC? It's like that, but for brew tag
inheritance priority.

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys

from argparse import ArgumentParser
from six.moves import zip as izip

from . import koji_cli_plugin, \
    NoSuchTag, PermissionException, GenericError


def renum_inheritance(inheritance, begin, step):
    """
    a new copy of the tag inheritance data, renumbered
    """

    renumbered = list()

    for index, inher in enumerate(inheritance):
        data = dict(inher)
        data['priority'] = begin + (index * step)
        renumbered.append(data)

    return renumbered


def cli_renum_tag(options):

    # todo, move these checks into the argument parser options. Sadly
    # we'll lose the snark, but it makes for cleaner code

    if options.begin < 0:
        raise GenericError("Inheritance priorities must be positive")
    elif options.begin > 1000:
        raise GenericError("Sensibilities offended. Use a lower begin"
                           " priority")
    elif options.step < 1:
        raise GenericError("Inheritance steps must be 1 or greater"
                           " (no reversing)")
    elif options.step > 100:
        raise GenericError("Chill out with the big numbers."
                           " Seriously. Relax.")

    session = options.session
    tagname = options.tagname

    if not session.getTag(tagname):
        raise NoSuchTag(tagname)

    original = session.getInheritanceData(tagname)
    renumbered = renum_inheritance(original, options.begin, options.step)

    if options.verbose:
        print("Renumbering inheritance priorities for", tagname)
        for left, right in izip(original, renumbered):
            name = left['name']
            lp = left['priority']
            rp = right['priority']
            print(" %3i -> %3i  %s" % (lp, rp, name))

    if options.test:
        print("Changes not committed in test mode.")

    else:
        # setting tag inheritance require admin, so let's make sure we
        # have that first.
        userinfo = session.getLoggedInUser()
        userperms = session.getUserPerms(userinfo["id"]) or ()

        if "admin" not in userperms:
            raise PermissionException()

        results = session.setInheritanceData(tagname, renumbered)
        if options.verbose and results:
            print(results)


def options_renum_tag(name):
    """
    [admin] Renumbers inheritance priorities of a tag, preserving order
    """

    from . import int_range

    parser = ArgumentParser(prog=name)
    addarg = parser.add_argument

    addarg("tag", action="store", metavar="TAGNAME",
           help="Tag to renumber")

    addarg("--verbose", action="store_true", default=False,
           help="Print information about what's changing")

    addarg("--test", action="store_true",  default=False,
           help="Calculate the new priorities, but don't commit"
           " the changes")

    addarg("--begin", action="store", type=int_range(0, 1000),
           default=10,
           help="New priority for first inheritance link"
           " (default: 10)")

    addarg("--step", action="store", type=int_range(1, 100),
           default=10,
           help="Priority increment for each subsequent"
           " inheritance link after the first (default: 10)")

    return parser


cli = koji_cli_plugin(options_renum_tag, cli_renum_tag)


# The end.
