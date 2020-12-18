#! /usr/bin/env python

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
Koji Smoky Dingo - a collection of Koji command-line features for
advanced users.

Note that this package needs the kojismokydingometa plugin to be
installed in order for the plugins to be loaded by the Koji CLI.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GPL version 3
"""


VERSION = "0.9.6"


CLASSIFIERS = [
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Software Development :: Build Tools",
]


COMMANDS = {
    "affected-targets": "kojismokydingo.cli.tags:AffectedTargets",
    "block-env-var": "kojismokydingo.cli.tags:BlockEnvVar",
    "block-rpm-macro": "kojismokydingo.cli.tags:BlockRPMMacro",
    "bulk-tag-builds": "kojismokydingo.cli.builds:BulkTagBuilds",
    "check-hosts": "kojismokydingo.cli.hosts:CheckHosts",
    "client-config": "kojismokydingo.cli.clients:ClientConfig",
    "cginfo": "kojismokydingo.cli.users:CGInfo",
    "filter-builds": "kojismokydingo.cli.builds:FilterBuilds",
    "latest-archives": "kojismokydingo.cli.archives:LatestArchives",
    "list-btypes": "kojismokydingo.cli.builds:ListBTypes",
    "list-build-archives": "kojismokydingo.cli.archives:ListBuildArchives",
    "list-cgs": "kojismokydingo.cli.builds:ListCGs",
    "list-component-builds": "kojismokydingo.cli.builds:ListComponents",
    "list-env-vars": "kojismokydingo.cli.tags:ListEnvVars",
    "list-rpm-macros": "kojismokydingo.cli.tags:ListRPMMacros",
    "list-tag-extras": "kojismokydingo.cli.tags:ListTagExtras",
    "perminfo": "kojismokydingo.cli.users:PermissionInfo",
    "remove-env-var": "kojismokydingo.cli.tags:RemoveEnvVar",
    "remove-rpm-macro": "kojismokydingo.cli.tags:RemoveRPMMacro",
    "renum-tag-inheritance": "kojismokydingo.cli.tags:RenumTagInheritance",
    "set-env-var": "kojismokydingo.cli.tags:SetEnvVar",
    "set-rpm-macro": "kojismokydingo.cli.tags:SetRPMMacro",
    "swap-tag-inheritance": "kojismokydingo.cli.tags:SwapTagInheritance",
    "userinfo": "kojismokydingo.cli.users:UserInfo",
}

CLI = {
    "ksd-filter-builds": "kojismokydingo.standalone.builds:ksd_filter_builds",
}


def config():
    return {
        "name": "kojismokydingo",
        "version": VERSION,
        "author": "Christopher O'Brien",
        "author_email": "obriencj@gmail.com",
        "description": "A collection of Koji client plugins and utils",
        "url": "https://github.com/obriencj/koji-smoky-dingo",

        "license": "GNU General Public License v3 (GPLv3)",

        "classifiers": CLASSIFIERS,

        "packages": [
            "koji_cli_plugins",
            "kojismokydingo",
            "kojismokydingo.cli",
            "kojismokydingo.sift",
            "kojismokydingo.standalone",
        ],

        "install_requires": [
            "koji",
            "six",
        ],

        "tests_require": [
            "docutils",
            "koji",
            "mock",
            "six",
        ],

        # The koji_cli_plugins namespace package needs to be a plain
        # directory that Koji can look through for individual plugins
        "zip_safe": False,

        "entry_points": {
            "koji_smoky_dingo": ["=".join(c) for c in COMMANDS.items()],
            "console_scripts":  ["=".join(c) for c in CLI.items()],
        },
    }


def setup():
    import setuptools
    return setuptools.setup(**config())


if __name__ == "__main__":
    setup()


#
# The end.
