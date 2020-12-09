from .type import Type

class Enum(Type):
    elem_type = None
    enum_type = None

    @classmethod
    def default(cls, *, ctx=None):
        return tuple(cls.enum_type.__members__.values())[0]

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.enum_type(cls.elem_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.elem_type.pack(value.value, ctx=ctx)

    @classmethod
    def _call(cls, elem_type, enum_type):
        return type(f"{elem_type.__name__}Enum", (cls,), dict(
            elem_type = elem_type,
            enum_type = enum_type,
        ))
