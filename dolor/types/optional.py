import inspect

from .type import Type
from .version_switched import handle_dict_type

class Optional(Type):
    elem_type = None
    exists    = None

    @classmethod
    def is_prefixed_by_type(cls):
        return isinstance(cls.exists, type) and issubclass(cls.exists, Type)

    @classmethod
    def has_function(cls):
        return inspect.isfunction(cls.exists)

    @classmethod
    def is_at_end(cls):
        return cls.exists is None

    @classmethod
    def _default(cls, *, ctx=None):
        if cls.has_function() and cls.exists(ctx.instance):
            return cls.elem_type.default(ctx=ctx)

        return None

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        if cls.has_function():
            if cls.exists(ctx.instance):
                return cls.elem_type.unpack(buf, ctx=ctx)
        elif cls.is_prefixed_by_type() and cls.exists.unpack(buf, ctx=ctx):
            return cls.elem_type.unpack(buf, ctx=ctx)
        elif cls.is_at_end():
            try:
                return cls.elem_type.unpack(buf, ctx=ctx)
            except:
                return None

        return None

    @classmethod
    def _pack(cls, value, *, ctx=None):
        if cls.has_function():
            if cls.exists(ctx.instance):
                return cls.elem_type.pack(value, ctx=ctx)

            return b""
        elif cls.is_prefixed_by_type():
            if value is not None:
                return cls.exists.pack(True, ctx=ctx) + cls.elem_type.pack(value, ctx=ctx)

            return cls.exists.pack(False, ctx=ctx)
        elif cls.is_at_end():
            if value is not None:
                return cls.elem_type.pack(value, ctx=ctx)

            return b""

        return b""

    @classmethod
    def _call(cls, elem_type, exists=None):
        elem_type = handle_dict_type(elem_type)

        if isinstance(exists, str):
            attr   = exists
            exists = lambda x: getattr(x, attr)

        return cls.make_type(f"{cls.__name__}{elem_type.__name__}",
            elem_type = elem_type,
            exists    = exists,
        )
