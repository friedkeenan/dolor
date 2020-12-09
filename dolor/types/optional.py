import inspect

from .type import Type
from .simple import Boolean

class Optional(Type):
    elem_type = None
    func = None

    @classmethod
    def is_prefixed_by_bool(cls):
        return cls.func is None

    @classmethod
    def has_function(cls):
        return inspect.isfunction(cls.func)

    @classmethod
    def default(cls, *, ctx=None):
        if cls.has_function() and cls.func(ctx.instance):
            return cls.elem_type.default(ctx=ctx)

        return None

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        if cls.has_function():
            if cls.func(ctx.instance):
                return cls.elem_type.unpack(buf, ctx=ctx)
        elif cls.is_prefixed_by_bool() and Boolean.unpack(buf, ctx=ctx):
            return cls.elem_type.unpack(buf, ctx=ctx)

        return None

    @classmethod
    def _pack(cls, value, *, ctx=None):
        if cls.has_function():
            if cls.func(ctx.instance):
                return cls.elem_type.pack(value, ctx=ctx)

            return b""
        elif cls.is_prefixed_by_bool():
            if value is not None:
                return Boolean.pack(True, ctx=ctx) + cls.elem_type.pack(value, ctx=ctx)

            return Boolean.pack(False, ctx=ctx)

        return b""

    @classmethod
    def _call(cls, elem_type, func=None):
        if isinstance(func, str):
            attr = func
            func = lambda x: getattr(x, attr)

        return type(f"Optional{elem_type.__name__}", (cls,), dict(
            elem_type = elem_type,
            func      = func,
        ))
