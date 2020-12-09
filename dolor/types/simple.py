import struct

from .. import util
from .type import Type

class SimpleType(Type):
    fmt = None

    @classmethod
    def real_fmt(cls):
        return f">{cls.fmt}"

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        ret = struct.unpack(cls.real_fmt(), buf.read(struct.calcsize(cls.real_fmt())))

        if len(ret) == 1:
            return ret[0]

        return ret

    @classmethod
    def _pack(cls, value, *, ctx=None):
        if util.is_iterable(value):
            return struct.pack(cls.real_fmt(), *value)

        return struct.pack(cls.real_fmt(), value)

class Boolean(SimpleType):
    _default = False
    fmt = "?"

class Byte(SimpleType):
    _default = 0
    fmt = "b"

class UnsignedByte(SimpleType):
    _default = 0
    fmt = "B"

class Short(SimpleType):
    _default = 0
    fmt = "h"

class UnsignedShort(SimpleType):
    _default = 0
    fmt = "H"

class Int(SimpleType):
    _default = 0
    fmt = "i"

class UnsignedInt(SimpleType):
    _default = 0
    fmt = "I"

class Long(SimpleType):
    _default = 0
    fmt = "q"

class UnsignedLong(SimpleType):
    _default = 0
    fmt = "Q"

class Float(SimpleType):
    _default = 0.0
    fmt = "f"

class Double(SimpleType):
    _default = 0.0
    fmt = "d"
