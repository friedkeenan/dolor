"""Numeric types.

The names for these types are based on the names from https://wiki.vg/
so that our :class:`~.Packet` definitions may use the same terminology,
despite the imprecise nature of the names.

All numeric types are big endian.
"""

import math
import pak

__all__ = [
    "Boolean",
    "Byte",
    "UnsignedByte",
    "Short",
    "UnsignedShort",
    "Int",
    "UnsignedInt",
    "Long",
    "UnsignedLong",
    "Float",
    "Double",
    "VarNumBufferLengthError",
    "VarNumOutOfRangeError",
    "VarNum",
    "VarInt",
    "VarLong",
    "Angle",
]

class Boolean(pak.Bool):
    """A single byte truth-value."""

    endian = ">"

class Byte(pak.Int8):
    """A signed 8-bit integer."""

    endian = ">"

class UnsignedByte(pak.UInt8):
    """An unsigned 8-bit integer."""

    endian = ">"

class Short(pak.Int16):
    """A signed 16-bit integer."""

    endian = ">"

class UnsignedShort(pak.UInt16):
    """An unsigned 16-bit integer."""

    endian = ">"

class Int(pak.Int32):
    """A signed 32-bit integer."""

    endian = ">"

class UnsignedInt(pak.UInt32):
    """An unsigned 32-bit integer."""

    endian = ">"

class Long(pak.Int64):
    """A signed 64-bit integer."""

    endian = ">"

class UnsignedLong(pak.UInt64):
    """An unsigned 64-bit integer."""

    endian = ">"

class Float(pak.Float32):
    """A 32-bit floating point value."""

    endian = ">"

class Double(pak.Float64):
    """A 64-bit floating point value."""

    endian = ">"

class VarNumBufferLengthError(Exception):
    """An error indicating the number of bytes read would exceed
    the allowed storage of a :class:`VarNum`.

    Parameters
    ----------
    var_num_cls : subclass of :class:`VarNum`
        The subclass whose storage would be exceeded.
    """

    def __init__(self, var_num_cls):
        super().__init__(f"'{var_num_cls.__name__}' cannot read beyond {var_num_cls._max_bytes} bytes")

class VarNumOutOfRangeError(Exception):
    """An error indicating a value is outside the range of a :class:`VarNum`'s possible values.

    Parameters
    ----------
    var_num_cls : subclass of :class:`VarNum`
        The subclass whose range ``value`` lies outside of.
    value : :class:`int`
        The value which exceeds the range.
    """

    def __init__(self, var_num_cls, value):
        super().__init__(f"Value '{value}' is out of the range of '{var_num_cls.__name__}'")

class VarNum(pak.Type):
    """A signed, variable-length integer.

    :meta no-undoc-members:

    Each byte of raw data contains 7 bits that contribute to the
    value of the integer, and 1 bit that indicates whether to
    read the next byte.

    When unpacking, if the number of bytes read would exceed the
    maximum number of bytes needed to read the specified :attr:`bits`,
    then a :exc:`VarNumBufferLengthError` is raised. This stops data
    from being read forever, potentially causing a denial of service.

    When packing, if the value to pack is outside the range of possible
    values for the specified :attr:`bits`, then a :exc:`VarNumOutOfRangeError`
    is raised. This stops values from being sent which may not be
    accurately received.

    Attributes
    ----------
    bits : :class:`int`
        The maximum number of bits the integer can contain.
    """

    _default = 0

    bits = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Calcululate the maximum number of bytes to read
        if cls.bits is not None:
            # Each byte has 7 value-bits, and 1 bit for whether to read the next byte.
            cls._max_bytes = math.ceil(cls.bits / 7)

            cls._value_range = range(-pak.util.bit(cls.bits - 1), pak.util.bit(cls.bits - 1))

    @classmethod
    def _unpack(cls, buf, *, ctx):
        num = 0

        for i in range(cls._max_bytes):
            read  = UnsignedByte.unpack(buf, ctx=ctx)

            # Get the bottom 7 bits
            value = read & 0b01111111

            num |= value << (7 * i)

            # If the top bit is not set, return
            if read & 0b10000000 == 0:
                return pak.util.to_signed(num, bits=cls.bits)

        raise VarNumBufferLengthError(cls)

    @classmethod
    def _pack(cls, value, *, ctx):
        # If 'value' is not an 'int' then checking if it's contained will
        # loop through the (very large) value range instead of just checking
        # comparisons.
        if not isinstance(value, int) or value not in cls._value_range:
            raise VarNumOutOfRangeError(cls, value)

        value = pak.util.to_unsigned(value, bits=cls.bits)

        data = b""

        while True:
            # Get the bottom 7 bits.
            to_write = value & 0b01111111

            value >>= 7
            if value != 0:
                # Set the top bit.
                to_write |= 0b10000000

            data += UnsignedByte.pack(to_write, ctx=ctx)

            if value == 0:
                return data

class VarInt(VarNum):
    """A signed, variable-length 32-bit integer."""

    bits = 32

class VarLong(VarNum):
    """A signed, variable-length 64-bit integer."""

    bits = 64

class Angle(pak.Type):
    """An angle whose value is in radians."""

    _default = 0.0

    @classmethod
    def _unpack(cls, buf, *, ctx):
        return math.tau * (UnsignedByte.unpack(buf, ctx=ctx) / 256)

    @classmethod
    def _pack(cls, value, *, ctx):
        return UnsignedByte.pack(round(256 * (value % math.tau) / math.tau), ctx=ctx)
