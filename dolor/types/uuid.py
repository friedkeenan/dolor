"""Types which represent UUIDs."""

import uuid
import pak

from .string import String

__all__ = [
    "UUIDString",
]

class UUIDString(pak.Type):
    """A UUID parsed from a :class:`~.String` representation."""

    # Length of string representation plus length byte.
    _size    = 36 + 1
    _default = uuid.UUID(int=0)

    _string_type = String(36)

    @classmethod
    def _unpack(cls, buf, *, ctx):
        return uuid.UUID(cls._string_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx):
        return cls._string_type.pack(str(value), ctx=ctx)
