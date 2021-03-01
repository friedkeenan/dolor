import math

from .. import util
from .type import Type
from .misc import StructType

class Boolean(StructType):
    """A boolean that corresponds to a single byte."""

    _default = False
    fmt      = "?"

class Byte(StructType):
    """A signed 8-bit integer."""

    _default = 0
    fmt      = "b"

class UnsignedByte(StructType):
    """An unsigned 8-bit integer."""

    _default = 0
    fmt      = "B"

class Short(StructType):
    """A signed 16-bit integer."""

    _default = 0
    fmt      = "h"

class UnsignedShort(StructType):
    """An unsigned 8-bit integer."""

    _default = 0
    fmt      = "H"

class Int(StructType):
    """A signed 32-bit integer."""

    _default = 0
    fmt      = "i"

class UnsignedInt(StructType):
    """An unsigned 32-bit integer."""

    _default = 0
    fmt      = "I"

class Long(StructType):
    """A signed 64-bit integer."""

    _default = 0
    fmt      = "q"

class UnsignedLong(StructType):
    """An unsigned 64-bit integer."""

    _default = 0
    fmt      = "Q"

class Float(StructType):
    """A 32-bit floating point value."""

    _default = 0.0
    fmt      = "f"

class Double(StructType):
    """A 64-bit floating point value."""

    _default = 0.0
    fmt      = "d"

class VarNum(Type):
    """A signed, variable-length integer.

    :meta no-undoc-members:

    To read the value, a byte is read, where the
    bottom 7 bits are a portion of the value, and
    the top bit indicates whether to read another
    byte and repeat the process.

    If the bytes read would exceed the number of
    bytes needed to get the necessary bits (as
    specified with the :attr:`bits` attribute),
    then a :exc:`ValueError` will be raised. This
    is done to prevent a DOS attack that sends
    bytes that always have the top bit set, leading
    to an infinite amount of bytes being read.

    Attributes
    ----------
    bits : :class:`int`
        The maximum amount of bits before a
        :exc:`ValueError` is raised.
    """

    _default = 0
    bits     = None

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        ret = 0

        for i in range(1 + cls.bits // 8):
            read = UnsignedByte.unpack(buf, ctx=ctx)
            value = read & 0x7f

            ret |= value << (7 * i)

            if read & 0x80 == 0:
                return util.to_signed(ret, bits=cls.bits)

        raise ValueError(f"{cls.__name__} is too big")

    @classmethod
    def _pack(cls, value, *, ctx=None):
        ret = b""

        for i in range(1 + cls.bits // 8):
            tmp = value & 0x7f

            value = util.urshift(value, 7, bits=cls.bits)
            if value != 0:
                tmp |= 0x80

            ret += UnsignedByte.pack(tmp, ctx=ctx)

            if value == 0:
                return ret

        raise ValueError(f"{cls.__name__} is too big")

class VarInt(VarNum):
    """A signed, variable-length 32-bit integer."""

    bits = 32

class VarLong(VarNum):
    """A signed, variable-length 64-bit integer."""

    bits = 64

class Angle(Type):
    """Represents an angle.

    The value is in radians.
    """

    _default = 0

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return math.tau * UnsignedByte.unpack(buf) / 256

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return UnsignedByte.pack(round(256 * (value % math.tau) / math.tau))
