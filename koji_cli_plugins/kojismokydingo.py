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
Koji Smoky Dingo - entry_points cli meta plugin

Uses python entry_points to load the actual koji command-line plugins
handler functions.

Koji Smoky Dingo provides some of its own handlers this way, but more
handlers can be defined this way using other installed packages with
entry_points.

:author: cobrien@redhat.com
"license: GPL version 3
"""


from __future__ import print_function


def __plugin__(glbls):

    import koji
    from pkg_resources import iter_entry_points
    from sys import stderr

    # in situations where koji.config is present and cli_entry_points
    # is explicitly set to False, we'll effective disable this
    # meta-plugin and not load any of the entry point cli commands.

    kconfig = getattr(koji, "config", None)
    if kconfig and not kconfig.getboolean("cli_entry_points", True):
        return

    commands = {}

    for entry_point in iter_entry_points('koji_cli_plugins'):
        name = entry_point.name

        try:
            handler_fn = entry_point.load()
            handler = handler_fn(name)

        except Exception as ex:
            message = "Error loading plugin %r" % entry_point
            print(message, ex, file=stderr)

        else:
            commands[handler.__name__] = handler

    glbls.update(commands)
    glbls["__all__"] = tuple(sorted(commands))


__plugin__(globals())


#
# The end.
