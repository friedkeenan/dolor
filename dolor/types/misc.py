import math
import uuid

from .type import Type
from .simple import UnsignedByte

class EmptyType(Type):
    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return None

    def __set__(self, instance, value):
        pass

    @classmethod
    def default(cls, *, ctx=None):
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

class Angle(Type):
    _default = 0

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return math.tau * UnsignedByte.unpack(buf) / 256

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return UnsignedByte.pack(round(256 * (value % math.tau) / math.tau))

class UUID(Type):
    _default = uuid.UUID(int=0)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return uuid.UUID(bytes=buf.read(0x10))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return value.bytes
