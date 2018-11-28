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
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <http://www.gnu.org/licenses/>.


"""
Meta plugin for Koji Smoky Dingo. Uses python entry_points to load
the actual koji command-line plugins.

author: cobrien@redhat.com
license: GPL version 3
"""


from __future__ import print_function


def __plugin__(glbls):

    import koji
    from koji.plugin import export_as
    from pkg_resources import iter_entry_points
    from sys import stderr

    kconfig = getattr(koji, "config", None)
    if not (kconfig and kconfig.getboolean("cli_entry_points", True)):
        return

    commands = {}

    for entry_point in pkg_resources.iter_entry_points('koji_cli_plugins'):
        name = entry_point.name

        try:
            handler_fn = entry_point.load()
            handler = handler_fn()

        except Exception as ex:
            message = "Exception while loading plugin %r (skipping)" % name
            print(message, ex, file=stderr)
            continue

        handler = export_as(name)(handler)
        commands[name] = handler

    glbls.update(commands)
    glbls["__all__"] = tuple(sorted(commands))


__plugin__(globals())
del __plugin__


#
# The end.
