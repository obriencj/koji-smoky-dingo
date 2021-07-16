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
Koji Smoky Dingo - Undocumented Magic

Internal-only. Undocumented. Don't rely on these in other
packages. API subject to abrupt change or removal.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import sys

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from inspect import currentframe
from os import getenv
from os.path import basename


__all__ = (
    "KSD_MERGE_PYI",
    "merge_annotations",
)


# Below this point are functions to asssist in merging .pyi type stubs
# into the actual .py modules at runtime. This is primarily used to
# allow sphinx to see the typing annotations without having to embed
# them directly in the real modules.

# We'll use the env var KSD_MERGE_PYI as a sentinel for the
# merge_signatures function. If not set to some agreeable value we
# won't perform the signature merging. We can turn it on during docs
# generation in order to get the typing data in our documentation, and
# then avoid it for normal runtime operation.
KSD_MERGE_PYI = getenv("KSD_MERGE_PYI", "").lower() in ("1", "true", "yes")


def _load_pyi(spec):
    """
    Given a module spec, import the matching .pyi as a separate module
    """

    # the base filename from the module we're loading stubs for
    py_file = basename(spec.origin)

    # we'll look for a resource in the same package with this filename
    pyi_file = py_file + "i"
    pyi_path = spec.loader.resource_path(pyi_file)

    # we'll pretend the .pyi file is a module named after the original
    # with a suffix _pyi_
    if spec.loader.is_package(spec.name):
        pyi_name = spec.name + "._pyi_"
    else:
        pyi_name = spec.name + "_pyi_"

    # load the stubs into a new module
    pyi_loader = SourceFileLoader(pyi_name, pyi_path)
    pyi_spec = spec_from_loader(pyi_name, pyi_loader)
    pyi_mod = module_from_spec(pyi_spec)

    # in order for relative imports to work from within the pyi we may
    # need the module to actually appear for a while.
    sys.modules[pyi_name] = pyi_mod
    try:
        pyi_spec.loader.exec_module(pyi_mod)
    finally:
        del sys.modules[pyi_name]

    return pyi_mod


def _merge_annotations(glbls, pyi_glbls):
    """
    Merge the annotations from pyi_glbls into glbls. Recurses into
    type declarations.
    """

    for key, pyi_thing in pyi_glbls.items():
        if key not in glbls or key.startswith("_"):
            continue

        thing = glbls[key]
        thing_anno = getattr(thing, '__annotations__', None)

        pyi_anno = getattr(pyi_thing, '__annotations__', None)

        if thing_anno is None:
            if pyi_anno is not None:
                thing.__annotations__ = pyi_anno

        elif pyi_anno is not None:
            thing_anno.update(pyi_anno)

        if isinstance(thing, type):
            # recur down type definitions in order to get annotations
            # for methods
            _merge_annotations(vars(thing), vars(pyi_thing))


def merge_annotations(force=False):
    """
    Merge PEP-0484 stub files into the calling module's annotations if
    the `KSD_MERGE_PYI` global is True. The value of `KSD_MERGE_PYI` is
    set at load time based on an environment variable of the same
    name.

    The .pyi file must be in the same path as the original .py file.

    :param force: perform annotation merging even if KSD_MERGE_PYI is
      not True
    """

    if not (force or KSD_MERGE_PYI):
        return

    back = currentframe().f_back
    assert back is not None, "merge_signatures invoked without parent frame"

    glbls = back.f_globals
    spec = glbls.get('__spec__')
    assert spec is not None, "merge_signatures invoked without module spec"

    # find and load the .pyi annotations as a module
    pyi_mod = _load_pyi(spec)

    # merge the annotations from the .pyi module globals into glbls
    _merge_annotations(glbls, vars(pyi_mod))

    # try and clean up after ourselves, don't want to leave a
    # reference to this function around in the calling module.
    try:
        del glbls["merge_annotations"]
    except KeyError:
        pass


#
# The end.
