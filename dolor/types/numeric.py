"""Numeric types.

The names for these types are based on the names from https://wiki.vg/
so that our packet definitions may use the same terminology, despite
the imprecise nature of the names.

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

class Angle(pak.Type):
    """An angle in radians."""

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return math.tau * (UnsignedByte.unpack(buf) / 256)

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return UnsignedByte.pack(round(256 * (value % math.tau) / math.tau))
