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


from __future__ import print_function

import sys

from json import dump


JSON_PRETTY_OPTIONS = {
    "indent": 4,
    "separators": (",", ": "),
    "sort_keys": True,
}


def pretty_json(data, output=sys.stdout, pretty=JSON_PRETTY_OPTIONS):
    dump(data, output, **pretty)
    print()


#
# The end.
