#! /usr/bin/env python3

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


from setuptools import setup


setup(
    name = "ksd-sieve",
    version = "2.0.0",

    description = "Example sifty sieves for Koji Sifty Dingo",
    license = "GNU General Public License v3 (GPLv3)",

    packages = [
        "ksd_sieve",
    ],

    install_requires = [
        "kojismokydingo",
    ],

    entry_points = {
        "koji_smoky_dingo_build_sieves": [
            "exec = ksd_sieve:ExecBuildSieve",
        ],
        "koji_smoky_dingo_tag_sieves": [
            "exec = ksd_sieve:ExecTagSieve",
        ],
    })


# The end.
