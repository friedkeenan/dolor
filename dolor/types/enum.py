"""Enumeration types."""

from .type import Type
from .util import prepare_types

class Enum(Type):
    elem_type = None
    enum_type = None

    @classmethod
    def _default(cls, *, ctx=None):
        return tuple(cls.enum_type.__members__.values())[0]

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.enum_type(cls.elem_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.elem_type.pack(value.value, ctx=ctx)

    @classmethod
    @prepare_types
    def _call(cls, elem_type: Type, enum_type):
        return cls.make_type(f"{elem_type.__name__}Enum({enum_type.__name__})",
            elem_type = elem_type,
            enum_type = enum_type,
        )
