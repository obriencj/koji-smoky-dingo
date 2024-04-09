# This implementation is essentially a no-op. We'll be using it only
# as a marker for the mypy_proxytype plugin itself.


from mypy.nodes import (
    Argument, Decorator, FuncDef, OverloadedFuncDef, SymbolTableNode, Var,
)
from mypy.plugin import ClassDefContext, MethodContext, Plugin

from typing import (
    Any, Callable, Generic, Optional, Type, TypeVar,
    overload,
)


__all__ = ( "proxytype", )


def _identity(o):
    return o


PT = TypeVar("PT")
RT = TypeVar("RT")


class ProxyTypeBuilder(Generic[PT, RT]):
    def __call__(self, cls: type) -> type:
        return cls


def proxytype(
        orig_class: Type[PT],
        return_wrapper: Type[RT]) -> ProxyTypeBuilder[PT, RT]:
    return _identity  # type: ignore


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
    cp.info = cls
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


PTB_CALL = (f"{ProxyTypeBuilder.__module__}."
            f"{ProxyTypeBuilder.__call__.__qualname__}")


class ProxyTypePlugin(Plugin):

    def __init__(self, options):
        super().__init__(options)
        self._proxytypes = {}


    def register_proxytype(self, ctx: MethodContext):
        args = ctx.type.args  # type: ignore
        if len(args) == 2:
            orig, virt = args
        else:
            orig = args[0]
            virt = None

        wrap = ctx.context.info  # type: ignore
        self._proxytypes[wrap.fullname] = (orig, virt)

        # TODO: was thinking I could just associate the type fullname
        # to its orig, virt vars and then use some other hook later to
        # update the class definition, but that's been a damn
        # struggle. So we're back to just decorating it immediately
        # here.

        decorate_proxytype(wrap, orig, virt)

        return ctx.default_return_type


    def get_method_hook(self, fullname: str):
        if fullname == PTB_CALL:
            return self.register_proxytype
        return None


def plugin(version: str):
    return ProxyTypePlugin


# The end.
