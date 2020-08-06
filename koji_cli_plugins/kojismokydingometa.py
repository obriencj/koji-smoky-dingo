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
Koji Smoky Dingo Meta Plugin

Uses python entry_points to load the actual koji command-line plugins
handler functions.

Koji Smoky Dingo provides some of its own handlers this way, but more
handlers can be defined this way using other installed packages with
entry_points.

To define additional commands, register an entry_point with the
koji_smoky_dingo group, using the name of the plugin. The entry point
should be a unary function which takes the name and returns a callable
object with the attributes that koji expects in a CLI plugin handler.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from __future__ import print_function


def __plugin__(glbls):
    # because koji will be inspecting the contents of this package, we
    # want to avoid leaving references around that it can see. So all
    # the action happens inside of this function.

    import koji
    import sys
    from pkg_resources import iter_entry_points

    # print("=== enter kojismokydingometa plugin ===", file=sys.stderr)

    # in situations where koji.config is present and koji_smoky_dingo
    # is explicitly set to False, we'll effective disable this
    # meta-plugin and not load any of the entry point cli commands.
    kconfig = getattr(koji, "config", None)
    if kconfig and not kconfig.getboolean("koji_smoky_dingo", True):
        return

    # we sort the entry points by module name so that duplicate
    # commands have a predictable resolution order
    points = sorted(iter_entry_points('koji_smoky_dingo'),
                    key=lambda e: e.module_name)

    for entry_point in points:
        # print(entry_point, file=sys.stderr)

        try:
            # each entry point when loaded should resolve to a unary
            # function. This function is then invoked with the name of
            # the entry point. The return value should be either None
            # or a callable appropriate for use as a koji command
            # handler.

            # Note we do not enforce the requirements for the entry
            # point packages -- those NEED to have been installed
            # ahead of time. We do this because we have a requirement
            # on koji, and in some cases koji is installed in a way
            # that the environment can find it, but pkg_resources is
            # oblivious to it.
            entry_fn = entry_point.load(require=False)
            handler = entry_fn(entry_point.name) if entry_fn else None

        except Exception as ex:
            # something has gone awry while either loading the entry
            # point, or while producing the cli handler from the unary
            # function that the entry point provided. We just announce
            # than an error happened and continue with the next
            # plugin.
            message = "Error loading plugin %r: %r" % (entry_point, ex)
            print(message, file=sys.stderr)

        else:
            # the handler, if available, is then combined into the
            # globals for the module. Thus, when the koji plugin
            # loader inspects the contents of this module, it will
            # find the handler with the appropriate name.
            if handler:
                glbls[handler.__name__] = handler


__plugin__(globals())
del __plugin__


#
# The end.
