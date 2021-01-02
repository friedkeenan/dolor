import uuid

from .type import Type
from .string import String

class UUID(Type):
    _default = uuid.UUID(int=0)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return uuid.UUID(bytes=buf.read(0x10))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return value.bytes

class UUIDString(Type):
    string_type = String(36)

    _default = uuid.UUID(int=0)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return uuid.UUID(cls.string_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.string_type.pack(str(value), ctx=ctx)
