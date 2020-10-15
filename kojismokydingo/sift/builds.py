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
Koji Smoky Dingo - Sifter filtering

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from koji import BUILD_STATES

from . import DEFAULT_SIEVES, PropertySieve, Sifter, ensure_int_or_str


__all__ = (
    "DEFAULT_BUILD_INFO_SIEVES",

    "NameSieve",
    "VersionSieve",
    "StateSieve",

    "build_info_sieves",
    "build_info_sifter",
)


class NameSieve(PropertySieve):
    name = "name"
    field = "name"


class VersionSieve(PropertySieve):
    name = "version"
    field = "version"


class StateSieve(PropertySieve):
    name = "state"
    field = "state"

    def __init__(self, sifter, pattern):
        pattern = ensure_int_or_str(pattern)
        if not isinstance(pattern, int):
            pattern = BUILD_STATES[pattern]
        super(PropertySieve, self).__init__(sifter, pattern)


DEFAULT_BUILD_INFO_SIEVES = [
    NameSieve,
    VersionSieve,
    StateSieve,
]


def build_info_sieves():
    sieves = []

    # TODO: grab some more via entry_points
    sieves.extend(DEFAULT_SIEVES)
    sieves.extend(DEFAULT_BUILD_INFO_SIEVES)

    return sieves


def build_info_sifter(src_str):
    return Sifter(build_info_sieves(), src_str)


#
# The end.
