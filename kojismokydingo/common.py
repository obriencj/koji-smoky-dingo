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

from collections import OrderedDict
from json import dump
from six.moves import range as xrange


JSON_PRETTY_OPTIONS = {
    "indent": 4,
    "separators": (",", ": "),
    "sort_keys": True,
}


def pretty_json(data, output=sys.stdout, pretty=JSON_PRETTY_OPTIONS):
    """
    Presents JSON in a pretty way.
    """

    dump(data, output, **pretty)
    print(file=output)


def resplit(arglist, sep=","):
    """
    Collapses comma-separated and multi-specified items into a single
    list. Useful with action="append" in an argparse argument.

    this allows arguments like:
    -x 1 -x 2, -x 3,4,5 -x ,6,7, -x 8

    to become
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    """

    work = (a.strip() for a in sep.join(arglist).split(sep))
    return [a for a in work if a]


def read_clean_lines(filename="-"):

    if not filename:
        return []

    elif filename == "-":
        fin = sys.stdin

    else:
        fin = open(filename, "r")

    lines = [line for line in (l.strip() for l in fin) if line]
    # lines = list(filter(None, map(str.strip, fin)))

    if filename != "-":
        fin.close()

    return lines


def unique(sequence):
    return list(OrderedDict.fromkeys(sequence))


def chunkseq(seq, chunksize):
    try:
        seqlen = len(seq)
    except TypeError:
        seq = list(seq)
        seqlen = len(seq)

    return (seq[offset:offset + chunksize] for
            offset in xrange(0, seqlen, chunksize))


#
# The end.
