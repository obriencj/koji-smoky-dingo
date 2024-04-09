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


from mypy.nodes import Decorator, FuncDef, OverloadedFuncDef, TypeInfo
from mypy.plugin import ClassDefContext, MethodContext, Plugin
from mypy.types import CallableType, Instance
from typing import Generic, List, Type, TypeVar, Union, cast, overload


__all__ = ( "proxytype", )


PT = TypeVar("PT")  # Original type to proxy
RT = TypeVar("RT")  # New return type
CT = TypeVar("CT")  # Class type to augment


class ProxyTypeBuilder(Generic[PT, RT]):
    # this class, and more specifically its __call__ method, are used
    # as the sentinel to trigger the mypy plugin hook.
    def __call__(self, cls: Type[CT]) -> Type[CT]:
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

    ```
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
    ```

    for example then, a method on ClientSession such as
      ``getPerms(self: ClientSession) -> List[str]``

    will be recreated on MultiCallSession as
      ``getPerms(self: MultiCallSession) -> VirtualCall[List[str]]``

    """

    # note that in our case, this is never actually used as a runtime
    # class decorator. We only ever "see" the koji typing stub when
    # running mypy, and then it's only for static analysis. So while
    # this impl does actually return an instance of a type if it were
    # run, it will never be run. The important part is that mypy will
    # see the type annotations of this decorator, and we'll be hooking
    # into the application of that to rummage and mutate the mypy
    # lexical internals to make it appear as if the decorated class
    # has all those methods.
    return ProxyTypeBuilder()


def clone_func(
        fn: FuncDef,
        cls: TypeInfo,
        returntype: Instance) -> FuncDef:

    tp = cast(CallableType, fn.type)
    cpt = tp.copy_modified()

    # overwrite self
    slf = cast(Instance, cpt.arg_types[0])
    slf = slf.copy_modified()
    slf.type = cls
    cpt.arg_types[0] = slf

    # overwrite return type
    if returntype is not None:
        n = returntype.copy_modified()
        n.args = (tp.ret_type, )
        cpt.ret_type = n

    cp = FuncDef(fn._name, None)
    cp.type = cpt
    cp.info = cls  # this particular field took so long to debug

    return cp


def clone_decorator(
        dec: Decorator,
        cls: TypeInfo,
        returntype: Instance) -> Decorator:

    cp = Decorator(clone_func(dec.func, cls, returntype),
                   dec.decorators, dec.var)
    cp.is_overload = dec.is_overload

    return cp


def clone_overloaded(
        ov: OverloadedFuncDef,
        cls: TypeInfo,
        returntype: Instance) -> OverloadedFuncDef:

    items: List[Union[Decorator, FuncDef]] = []
    for item in ov.items:
        if isinstance(item, Decorator):
            item = clone_decorator(item, cls, returntype)
        elif isinstance(item, FuncDef):
            item = clone_func(item, cls, returntype)
        items.append(item)

    cp = OverloadedFuncDef(items)
    cp._fullname = ov.fullname

    return cp


def decorate_proxytype(wrap: TypeInfo, orig: Instance, virt: Instance):
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

        node = sym.node
        if isinstance(node, FuncDef):
            nsym = sym.copy()
            nsym.node = clone_func(node, wrap, virt)
            wrap.names[name] = nsym

        elif isinstance(node, OverloadedFuncDef):
            nsym = sym.copy()
            nsym.node = clone_overloaded(node, wrap, virt)
            wrap.names[name] = nsym


def handle_proxytype_hook(ctx: MethodContext):
    wrap = ctx.context.info     # type: ignore
    orig, virt = ctx.type.args  # type: ignore

    decorate_proxytype(wrap, orig, virt)

    return ctx.default_return_type


class ProxyTypePlugin(Plugin):

    def get_method_hook(self, fullname: str):
        if fullname == PTB_CALL:
            return handle_proxytype_hook
        return None


def plugin(version: str):
    # mypy plugin loading point

    return ProxyTypePlugin


# The end.
