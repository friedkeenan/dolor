import struct

from .. import util
from .type import Type

class EmptyType(Type):
    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return None

    def __set__(self, instance, value):
        pass

    @classmethod
    def _default(cls, *, ctx=None):
        return None

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return None

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return b""

class RawByte(Type):
    _default = b"\x00"

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        ret = buf.read(1)

        if len(ret) < 1:
            raise ValueError("Buffer ran out of bytes")

        return ret

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return bytes(value[:1])

class StructType(Type):
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
