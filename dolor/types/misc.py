"""Miscellaneous types."""

import struct

from .. import util
from .type import Type

class EmptyType(Type):
    """A type of no value.

    It always unpacks to ``None`` and always packs
    to ``b""``.

    Users should not have to explicitly use this
    type; it is just useful for things like
    :class:`~.VersionSwitchedType` for instance,
    which uses this type when a packet attribute
    doesn't exist for a certain version.
    """

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
    """A single byte of data.

    The main reason this exists is to be used
    along with :class:`~.Array`, for which this
    type is special-cased to produce a
    :class:`bytearray` value.
    """

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
    """A wrapper over :func:`struct.pack` and :func:`struct.unpack`.

    :meta no-undoc-members:

    Attributes
    ----------
    fmt : :class:`str`
        The format string for the structure, not including
        the endianness prefix.
    """

    fmt = None

    @classmethod
    def real_fmt(cls):
        """Translates the :attr:`fmt` attribute to the format string actually used.

        Just adds the big endian prefix to the format string,
        as all Minecraft types are big endian.
        """

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
