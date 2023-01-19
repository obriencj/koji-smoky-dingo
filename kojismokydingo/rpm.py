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
Koji Smoky Dingo - RPM NEVRA Utils

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import re

from itertools import zip_longest
from typing import Tuple, cast


__all__ = (
    "evr_compare",
    "evr_split",
    "nevr_split",
    "nevra_split",
)


_rpm_str_split_re = re.compile(r"(~?(?:\d+|[a-zA-Z]+))").split


def _rpm_str_split(s: str) -> Tuple[str]:
    """
    Split an E, V, or R string for comparison by its segments
    """

    return tuple(i for i in _rpm_str_split_re(s)  # type: ignore
                 if (i.isalnum() or i.startswith("~")))


def _rpm_str_compare(leftstr: str, rightstr: str) -> int:
    """
    Comparison of left and right by RPM version comparison rules.

    Either string should be *one* element of the EVR tuple (ie. either the
    epoch, version, or release). Comparison will split the element on RPM's
    special delimeters.

    :since: 2.0
    """

    left: Tuple[str] = _rpm_str_split(leftstr)
    right: Tuple[str] = _rpm_str_split(rightstr)

    lp: str
    rp: str

    for lp, rp in zip_longest(left, right, fillvalue=""):

        # Special comparison for tilde segments
        if lp.startswith("~"):
            # left is tilde

            if rp.startswith("~"):
                # right also is tilde, let's just chop off the tilde
                # and fall through to non-tilde comparisons below

                lp = lp[1:]
                rp = rp[1:]

            else:
                # right is not tilde, therefore right is greater
                return -1

        elif rp.startswith("~"):
            # left is not tilde, but right is, therefore left is greater
            return 1

        # Special comparison for digits vs. alphabetical
        if lp.isdigit():
            # left is numeric

            if rp.isdigit():
                # left and right are both numeric, convert and fall
                # through
                ilp = int(lp)
                irp = int(rp)
                if ilp == irp:
                    continue
                else:
                    return 1 if ilp > irp else -1

            else:
                # right is alphabetical or absent, left is greater
                return 1

        elif rp.isdigit():
            # left is alphabetical but right is not, right is greater
            return -1

        # Final comparison for segment
        if lp == rp:
            # left and right are equivalent, check next segment
            continue
        else:
            # left and right are not equivalent
            return 1 if lp > rp else -1

    else:
        # ran out of segments to check, must be equivalent
        return 0


def evr_compare(
        left_evr: Tuple[str, str, str],
        right_evr: Tuple[str, str, str]) -> int:
    """
    Compare two (Epoch, Version, Release) tuples.

    This is an alternative implementation of the rpm lib's
    labelCompare function.

    Return values:

    * 1 if left_evr is greater-than right_evr
    * 0 if left_evr is equal-to right_evr
    * -1 if left_evr is less-than right_evr

    :param left_evr: The left Epoch, Version, Release for comparison

    :param right_evr: The right Epoch, Version, Release for comparison

    :since: 2.0
    """

    for lp, rp in zip_longest(left_evr, right_evr, fillvalue="0"):
        if lp == rp:
            # fast check to potentially skip all the matching
            continue

        compared = _rpm_str_compare(lp, rp)
        if compared:
            # non zero comparison for segment, done checking
            return compared

    else:
        # ran out of segments to check, must be equivalent
        return 0


def nevra_split(nevra: str) -> Tuple[str, str, str, str, str]:
    """
    Splits an NEVRA into a five-tuple representing the name, epoch,
    version, release, and arch.

    If name, epoch, arch, or release are absent, they are represented
    as a ``None``

    This differs from NEVRA splitting in that the last dotted segment
    of the release is considered to be the architecture. Because there
    may be 1 or more dotted segments to a release, it's impossible to
    determine whether the final segment is an arch or not simply from
    the structure. However, a valid NEVRA will always have at least
    two segments -- the last will be the architecture.

    Valid RPM NEVRA is in the following layout:

    eg. ``"bind-32:9.10.2-2.P1.fc22.x86_64"``

    * name: ``"bind"``
    * epoch: ``"32"``
    * version: ``"9.10.2"``
    * release: ``"2.P1.fc22"``
    * arch: ``"x86_64"``

    :since: 2.0
    """

    name, epoch, version, release = nevr_split(nevra)

    if release and "." in release:
        release, arch = release.rsplit(".", 1)
    else:
        arch = None

    return name, epoch, version, release, arch


def nevr_split(nevr: str) -> Tuple[str, str, str, str]:
    """
    Splits an NEVR into a four-tuple represending the name, epoch,
    version, and release.

    If name, epoch, or release are absent they are represented as
    ``None``

    This differs from NEVRA splitting in that the last dotted segment
    of the release is not considered an architecture. Because there
    may be 1 or more dotted segments to a release, it's impossible to
    determine whether the final segment is an arch or not simply from
    the structure.

    Valid RPM NEVRA is in the following layout:

    eg. ``"bind-32:9.10.2-2.P1.fc22"``

    * name: ``"bind"``
    * epoch: ``"32"``
    * version: ``"9.10.2"``
    * release: ``"2.P1.fc22"``

    :since: 2.0
    """

    epoch, version, release = evr_split(nevr)

    if epoch:
        if "-" in epoch:
            name, epoch = epoch.rsplit("-", 1)
        else:
            name = None
    else:
        name = version
        if release and "-" in release:
            version, release = release.split("-", 1)
        else:
            version = release
            release = None

    return name, epoch, version, release


def evr_split(evr: str) -> Tuple[str, str, str]:
    """
    Splits an EVR into a dict with the keys epoch, version, and release.

    If epoch is omitted, it is presumed to be ``"0"``
    If release is omitted, it is presumed to be ``None``

    Valid RPM EVR is in the following layout:

    eg. ``"32:9.10.2-2.P1.fc22"``

    * epoch: ``"32"``
    * version: ``"9.10.2"``
    * release: ``"2.P1.fc22"``

    :since: 2.0
    """

    version = evr

    if ":" in version:
        epoch, version = version.split(":", 1)
    else:
        epoch = None

    if "-" in version:
        version, release = version.split("-", 1)
    else:
        release = None

    return epoch, version, release


#
# The end.
