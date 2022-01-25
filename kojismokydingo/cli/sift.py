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
Some CLI adapters for working with Sifty Dingo filtering

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import os

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from functools import partial
from operator import attrgetter, itemgetter
from os.path import basename
from pkg_resources import EntryPoint, iter_entry_points
from typing import Callable, Dict, Iterable, List, Optional, Type

from . import open_output, printerr, resplit
from ..common import escapable_replace
from ..sift import DEFAULT_SIEVES, Sieve, Sifter, SifterError
from ..sift.builds import build_info_sieves
from ..sift.tags import tag_info_sieves
from ..types import KeySpec


__all__ = (
    "BuildSifting",
    "Sifting",
    "TagSifting",

    "output_sifted",
)


OnErr = Callable[[EntryPoint, Exception], None]


def _entry_point_sieves(
        key: str,
        on_err: Optional[OnErr] = None) -> List[Type[Sieve]]:
    """
    Load all Sieve instances from entry points using the given
    key. Returns a list of Sieve subclasses that can be used to
    augment the predicates in a Sifter.

    The individual endpoints can resolve to any of the following:
     * a Sieve subclass
     * a list or tuple of Sieve subclasses
     * a callable which returns a Sieve subclass
     * a callable which returns a list or tuple of Sieve subclasses

    The entry points are sorted by their module name and name, and
    the results are combined into a list.

    If on_err is None, then any exceptions raised during the
    resolution of entry points into Sieves will simply be skipped.

    If on_err is not None, then is must be a callable that accepts two
    arguments: an entry point and an exception. This callable will be
    invoked if there is an exception raised during the resolution of
    the entry point into Sieves. If the callable returns True, loading
    of any additional entry points will continue. Otherwise no further
    entry points will be loaded.

    :param key: entry point key to load

    :param on_err: error handling function
    """

    points = sorted(iter_entry_points(key),
                    key=attrgetter('module_name', 'name'))

    collected = []

    for entry_point in points:
        try:
            ep_ref = entry_point.load()

            # is this TOO flexible? The entry point can load as
            # any of:
            #  * Sieve subclass
            #  * list/tuple of Sieve subclasses
            #  * null arity callable which returns the above

            if issubclass(ep_ref, Sieve):
                collected.append(ep_ref)
                continue

            if callable(ep_ref):
                ep_ref = ep_ref()

            if isinstance(ep_ref, (list, tuple)):
                collected.extend(ep_ref)
            elif issubclass(ep_ref, Sieve):
                collected.append(ep_ref)
            else:
                pass

        except Exception as ex:
            if on_err and not on_err(entry_point, ex):
                break

    return collected


def entry_point_tag_info_sieves(
        on_err: Optional[OnErr] = None) -> List[Type[Sieve]]:
    return _entry_point_sieves("koji_smoky_dingo_tag_sieves", on_err)


def entry_point_build_info_sieves(
        on_err: Optional[OnErr] = None) -> List[Type[Sieve]]:
    return _entry_point_sieves("koji_smoky_dingo_build_sieves", on_err)


class Sifting():
    """
    A mixin for SmokyDingo instances that wish to offer a sifter.
    """

    def sifter_arguments(
            self,
            parser: ArgumentParser) -> ArgumentParser:
        """
        Adds an argument group for for loading a Sifter from either an
        text argument or a filename, and specifying output files for
        the expected flags from that Sifter's results.

         * ``--output/-o FLAG:FILENAME[,...]``
         * ``--filter FILTER``
         * ``--filter-file FILTER_FILE``
        """

        grp = parser.add_argument_group("Filtering with Sifty sieves")
        addarg = grp.add_argument

        addarg("--param", "-P", action="append", default=list(),
               dest="params", metavar="KEY=VALUE",
               help="Provide compile-time values to the sifty"
               " filter expressions")

        addarg("--env-params", action="store_true", default=False,
               dest="use_env",
               help="Use environment vars for params left unassigned")

        addarg("--output", "-o", action="append", default=list(),
               dest="outputs", metavar="FLAG:FILENAME",
               help="Divert results marked with the given FLAG to"
               " FILENAME. If FILENAME is '-', output to stdout."
               " The 'default' flag is output to stdout by default,"
               " and other flags are discarded")

        addarg("--no-entry-points", "-n", action="store_false", default=True,
               dest="entry_points",
               help="Disable loading of additional sieves from"
               " entry_points")

        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--filter", action="store", default=None,
               metavar="FILTER",
               help="Use the given sifty filter predicates")

        addarg("--filter-file", action="store", default=None,
               metavar="FILTER_FILE",
               help="Load sifty filter predictes from file")

        return parser


    def default_params(self) -> Dict[str, str]:
        params: Dict[str, str]
        params = getattr(self, "_sifter_params", None)
        if params is None:
            self._sifter_params = params = {}  # type: ignore
        return params


    def get_params(
            self,
            options: Namespace) -> Dict[str, str]:

        cli_params: Dict[str, str]
        env_params: Dict[str, str]
        params: Dict[str, str]

        # build up a params dict based on command-line options, param
        # definitions from the filter file, and finally the
        # environment if the --env flag was set.
        cli_params = options.params
        env_params = os.environ if options.use_env else {}  # type: ignore
        params = self.default_params()

        for opt in resplit(cli_params):
            if "=" in opt:
                key, val = opt.split("=", 1)
            else:
                key = opt
                val = None
            params[key] = val

        for key, val in params.items():
            if val is None:
                if key in env_params:
                    params[key] = env_params[key]
                else:
                    raise SifterError(f"param {key} is not defined")

        return params


    def get_outputs(
            self,
            options: Namespace) -> Dict[str, str]:
        """
        Produces a dict mapping flag names to output files based on the
        accumulated results of the ``--output FLAG:FILENAME`` argument.

        This dict can be used with `output_sifted` to record the results
        of a sifter to a collection of files.
        """

        result: Dict[str, str] = {}
        newresult: Dict[str, str]

        for opt in resplit(options.outputs):
            if ":" in opt:
                flag, dest = opt.split(":", 1)
            else:
                flag = opt
                dest = "-"
            result[flag] = dest or None

        if "*" in result:
            # the * output means that all otherwise-undefined flag
            # outputs should be directed there, but we don't actually
            # know all the flags at this point. So we'll create a
            # defaultdict that produces that value for misses,
            # pre-populate it with the output mappings we know of
            overall = result.pop("*")
            newresult = defaultdict(lambda: overall)
            newresult.update(result)
            result = newresult

        elif "default" not in result:
            result["default"] = "-"

        return result


    def get_sieves(
            self,
            entry_points: bool = True) -> List[Type[Sieve]]:
        return DEFAULT_SIEVES


    def get_sifter(
            self,
            options: Namespace) -> Sifter:
        """
        Produces a Sifter instances constructed from values in options.
        These options should have been generated from a parser that
        has had the `Sifting.sifter_arguments` invoked on it.
        """

        if options.filter:
            filter_src = options.filter
        elif options.filter_file:
            with open(options.filter_file, "rt") as fin:
                filter_src = fin.read()
        else:
            return None

        params = self.get_params(options)
        sieves = self.get_sieves(options.entry_points)
        return Sifter(sieves, filter_src, params=params)


def _report_problem(msg, entry_point, exc):
    # printerr(msg % (entry_point, exc))
    printerr(msg.format(entry_point, exc))
    return True


class BuildSifting(Sifting):

    def get_sieves(self, entry_points=True):
        sieves = build_info_sieves()

        if entry_points:
            msg = "Error loading build sieve from entry_point {} : {}"
            err = partial(_report_problem, msg)
            sieves.extend(entry_point_tag_info_sieves(on_err=err))

        return sieves


class TagSifting(Sifting):

    def get_sieves(self, entry_points=True):
        sieves = tag_info_sieves()

        if entry_points:
            msg = "Error loading tag sieve from entry_point {} : {}"
            err = partial(_report_problem, msg)
            sieves.extend(entry_point_tag_info_sieves(on_err=err))

        return sieves


def output_sifted(
        results: Dict[str, List[dict]],
        key: KeySpec = "id",
        outputs: Optional[Dict[str, str]] = None,
        sort: Optional[KeySpec] = None):
    """
    Records the results of a sifter to output. As sifter results are
    dicts, the `key` parameter can be either a unary callable or an
    index value to be used to fetch a simplified, printable
    representaiton from the dicts.

    `outputs` is a mapping of flag names to filenames using the rules
    of the :py:func:`open_output` function.

    :param results: results of invoking a Sifter on a set of data

    :param key: transformation to apply to the individual data
      elements prior to recording. Default, lookup the ``"id"`` index
      from the element.

    :param outputs: mapping of flags to destination filenames. If
      unspecified, the default flag will be written to stdout and the
      rest will be discarded.

    :param sort: sorting to apply to the results in each flag. If
      unspecified, order is preserved.
    """

    if not callable(key):
        key = itemgetter(key)

    if sort and not callable(sort):
        sort = partial(sorted, key=itemgetter(sort))

    if outputs is None:
        outputs = {"default": "-"}

    # kinda hackish but we need to populate the defaults in this case
    # because we really want to iterate over the outputs, not the
    # results in order to make sure every output gets written to, even
    # if it has no results.
    if isinstance(outputs, defaultdict):
        for flag in results:
            dest = outputs[flag]

    for flag, dest in outputs.items():
        if "%" in dest:
            safe_flag = flag.translate(str.maketrans("/\\ ", "___"))
            dest = escapable_replace(dest, "%", safe_flag)

        if dest.startswith("@"):
            dest = dest[1:]
            append = True
        else:
            append = False

        flagged = results.get(flag, ())
        if sort:
            flagged = sort(flagged)

        with open_output(dest, append) as dout:
            for res in map(key, flagged):
                print(res, file=dout)


#
# The end.
