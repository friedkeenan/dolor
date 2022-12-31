import math
import pak
import pytest

from dolor import *

# We avoid testing basic numeric types that simply
# inherit from pak types, since that would amount to
# testing the library when that is not our responsibility.

def test_var_int():
    pak.test.type_behavior(
        types.VarInt,

        (0,         b"\x00"),
        (1,         b"\x01"),
        (2**7 - 1,  b"\x7F"),
        (2**7,      b"\x80\x01"),
        (2**8 - 1,  b"\xFF\x01"),
        (2**31 - 1, b"\xFF\xFF\xFF\xFF\x07"),
        (-1,        b"\xFF\xFF\xFF\xFF\x0F"),
        (-2**31,    b"\x80\x80\x80\x80\x08"),

        static_size = None,
        default     = 0,
    )

    with pytest.raises(types.VarNumBufferLengthError):
        types.VarInt.unpack(b"\x80\x80\x80\x80\x80")

    with pytest.raises(types.VarNumOutOfRangeError):
        types.VarInt.pack(2**31)

    with pytest.raises(types.VarNumOutOfRangeError):
        types.VarInt.pack(-2**31 - 1)

    with pytest.raises(types.VarNumOutOfRangeError):
        types.VarInt.pack(None)

def test_var_long():
    pak.test.type_behavior(
        types.VarLong,

        (0,         b"\x00"),
        (1,         b"\x01"),
        (2**7 - 1,  b"\x7F"),
        (2**7,      b"\x80\x01"),
        (2**8 - 1,  b"\xFF\x01"),
        (2**63 - 1, b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x7F"),
        (-1,        b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01"),
        (-2**63,    b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x01"),

        static_size = None,
        default     = 0,
    )

    with pytest.raises(types.VarNumBufferLengthError):
        types.VarLong.unpack(b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80")

    with pytest.raises(types.VarNumOutOfRangeError):
        types.VarLong.pack(2**63)

    with pytest.raises(types.VarNumOutOfRangeError):
        types.VarLong.pack(-2**63 - 1)

def test_angle():
    pak.test.type_behavior(
        types.Angle,

        (math.tau * 0 / 8, b"\x00"),
        (math.tau * 1 / 8, b"\x20"),
        (math.tau * 2 / 8, b"\x40"),
        (math.tau * 3 / 8, b"\x60"),
        (math.tau * 4 / 8, b"\x80"),
        (math.tau * 5 / 8, b"\xA0"),
        (math.tau * 6 / 8, b"\xC0"),
        (math.tau * 7 / 8, b"\xE0"),

        static_size = 1,
        default     = 0.0,
    )

    # These must be checked outside the above call since
    # when they are marshaled back to values, they will
    # be from 0 to tau.
    assert types.Angle.pack(math.tau * 8 / 8) == b"\x00"
    assert types.Angle.pack(math.tau * 9 / 8) == b"\x20"

    assert isinstance(types.Angle.default(), float)

    assert types.Angle.default() == 0
