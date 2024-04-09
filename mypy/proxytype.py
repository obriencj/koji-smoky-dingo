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
proxytype - a mypy plugin and decorator

The `proxytype.proxytype` class decorator is for use in cases where we
need to provide static typing information for a class that dynamically
proxies the methods of some other class. In our case that is
specifically for the behavior of koji.MultiCallSession proxying to
koji.ClientSession

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from mypy.nodes import Decorator, FuncDef, OverloadedFuncDef
from mypy.plugin import ClassDefContext, MethodContext, Plugin
from typing import Generic, Type, TypeVar, overload


__all__ = ( "proxytype", )


PT = TypeVar("PT")
RT = TypeVar("RT")


class ProxyTypeBuilder(Generic[PT, RT]):
    # this class, and more specifically its __call__ method, are used
    # as the sentinel to trigger the mypy plugin hook.
    def __call__(self, cls: type) -> type:
        return cls


# This string needs to refer to the fully-qualified identifier for the
# above class, which stands as our sentinel to trigger the plugin's
# behavior.
PTB_CALL = "proxytype.ProxyTypeBuilder.__call__"


def proxytype(
        orig_class: Type[PT],
        return_wrapper: Type[RT]) -> ProxyTypeBuilder[PT, RT]:

    """
    class decorator which, via its ProxyTypeBuilder return type,
    triggers augmentation of its wrapper class with the methods found
    in the orig_class type, having their first (self) argument changed
    to match the decorated class, and their return type to match the
    return_wrapper's generic

    The canonical example is MultiCallSession, eg.

    ``
    class ClientSession:
        # lots of methods here
        ...

    class VirtualCall(Generic[T]):
        result: T

    @proxytype(ClientSession, VirtualCall)
    class MultiCallSession:
        # all methods from ClientSession magically copied into
        # this during static analysys
        ...
    ``

    for example then, a method on ClientSession such as
      ``getPerms(self: ClientSession) -> List[str]``

    will be recreated on MultiCallSession as
      ``getPerms(self: MultiCallSession) -> VirtualCall[List[str]]``

    """
    return ProxyTypeBuilder()


def clone_func(fn, cls, returntype):
    cpt = fn.type.copy_modified()

    # overwrite self
    cpt.arg_types[0] = cpt.arg_types[0].copy_modified()
    cpt.arg_types[0].type = cls

    # overwrite return type
    if returntype is not None:
        n = returntype.copy_modified()
        n.args = (fn.type.ret_type, )
        cpt.ret_type = n

    cp = FuncDef(fn._name, None)
    cp.type = cpt
    cp.info = cls  # this particular field took so long to debug
    # cp._fullname = fn.fullname

    return cp


def clone_decorated(dec, cls, returntype):
    cp = Decorator(clone_func(dec.func, cls, returntype),
                   dec.decorators, dec.var)

    cp.is_overload = dec.is_overload

    return cp


def clone_overload(ov, cls, returntype):
    items = [clone_decorated(i, cls, returntype) for i in ov.items]
    cp = OverloadedFuncDef(items)
    cp._fullname = ov.fullname

    return cp


def decorate_proxytype(wrap, orig, virt):
    """
    Creates methods on wrap cloned from orig, modified to return
    virt wrappers.

    :param wrap: the type definition as decorated by
    ``@proxytype(orig, virt)``

    :param orig: the type definition to copy fields from

    :param virt: the type definition for wrapping the original result
    types in
    """

    for name, sym in orig.type.names.items():
        if name.startswith("_"):
            continue

        if isinstance(sym.node, FuncDef):
            nsym = sym.copy()
            nsym.node = clone_func(nsym.node, wrap, virt)
            wrap.names[name] = nsym

        elif isinstance(sym.node, OverloadedFuncDef):
            nsym = sym.copy()
            nsym.node = clone_overload(nsym.node, wrap, virt)
            wrap.names[name] = nsym

    return None


class ProxyTypePlugin(Plugin):

    def register_proxytype(self, ctx: MethodContext):
        args = ctx.type.args  # type: ignore
        if len(args) == 2:
            orig, virt = args
        else:
            orig = args[0]
            virt = None

        wrap = ctx.context.info  # type: ignore
        decorate_proxytype(wrap, orig, virt)

        return ctx.default_return_type


    def get_method_hook(self, fullname: str):
        if fullname == PTB_CALL:
            return self.register_proxytype
        return None


def plugin(version: str):
    # mypy plugin loading point

    return ProxyTypePlugin


# The end.
