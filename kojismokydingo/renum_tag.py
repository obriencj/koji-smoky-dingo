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
Koji Smoky Dingo - admin command renum-tag

Remember RENUM from BASIC? It's like that, but for brew tag
inheritance priority.

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

from six.moves import zip as izip

from . import AdminSmokyDingo, NoSuchTag


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


def cli_renum_tag(session, tagname, begin=10, step=10,
                  verbose=False, test=False):

    if not session.getTag(tagname):
        raise NoSuchTag(tagname)

    original = session.getInheritanceData(tagname)
    renumbered = renum_inheritance(original, begin, step)

    if verbose:
        print("Renumbering inheritance priorities for", tagname)
        for left, right in izip(original, renumbered):
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


class cli(AdminSmokyDingo):

    description = "Renumbers inheritance priorities of a tag," \
                  " preserving order"


    def parser(self):
        parser = super(cli, self).parser()
        addarg = parser.add_argument

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

        return parser


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
        return cli_renum_tag(options.session, options.tagname,
                             options.begin, options.step,
                             options.verbose, options.test)


#
# The end.
