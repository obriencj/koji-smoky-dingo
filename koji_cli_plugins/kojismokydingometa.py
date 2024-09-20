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

Uses python entry_points to load the actual koji command-line plugin
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


def __plugin__(glbls):
    # because koji will be inspecting the contents of this package, we
    # want to avoid leaving references around that it can see. So all
    # the action happens inside of this function.

    from operator import attrgetter
    from os import getenv
    from sys import stderr, version_info

    if version_info < (3, 11):
        from pkg_resources import iter_entry_points
        ep_key = attrgetter('module_name', 'name')

    else:
        from importlib.metadata import entry_points as _entry_points

        def iter_entry_points(group):
            return _entry_points(group=group)

        ep_key = attrgetter('module', 'name')

    # these env var checks were introduced in v2.2.0
    verbose = getenv("KSD_VERBOSE", None) == "1"
    explode = getenv("KSD_EXPLODE", None) == "1"

    # we sort the entry points by module name so that duplicate
    # commands have a predictable resolution order
    points = sorted(iter_entry_points('koji_smoky_dingo'),
                    key=ep_key)

    for entry_point in points:
        try:
            # each entry point when loaded should resolve to a unary
            # function. This function is then invoked with the name of
            # the entry point. The return value should be either None
            # or a callable appropriate for use as a koji command
            # handler. See `kojismokydingo.types.CLIHandler`

            if version_info < (3, 11):
                entry_fn = entry_point.resolve()
            else:
                entry_fn = entry_point.load()

            handler = entry_fn(entry_point.name) if entry_fn else None

        except Exception as ex:
            # something has gone awry while either loading the entry
            # point, or while producing the cli handler from the unary
            # function that the entry point provided.

            if verbose:
                # when KSD_VERBOSE=1 we announce than an error happened
                message = f"Error loading plugin {entry_point!r}: {ex!r}"
                print(message, file=stderr)

            if explode:
                # when KSD_EXPLODE=1 we allow the exception to be
                # raised all the way up. Otherwise we'll just continue
                # on to the next entrypoint and allow for normal CLI
                # execution
                raise

        else:
            # the handler, if available, is then combined into the
            # globals for the module. Thus, when the koji plugin
            # loader inspects the contents of this module, it will
            # find the handler with the appropriate name.
            if handler and getattr(handler, "enabled", True):
                glbls[handler.__name__] = handler


__plugin__(globals())
del __plugin__


#
# The end.
