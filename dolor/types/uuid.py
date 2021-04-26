"""UUID types."""

import uuid

from .type import Type
from .string import String

class UUID(Type):
    """A UUID parsed from 16 bytes of data."""

    _default = uuid.UUID(int=0)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return uuid.UUID(bytes=buf.read(0x10))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return value.bytes

class UUIDString(Type):
    """A UUID parsed from a string representation."""

    string_type = String(36)

    _default = uuid.UUID(int=0)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return uuid.UUID(cls.string_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.string_type.pack(str(value), ctx=ctx)
