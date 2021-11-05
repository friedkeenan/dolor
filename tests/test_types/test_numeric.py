import math

from dolor import *

from ..util import assert_type_marshal

# We avoid testing basic numeric types that simply
# inherit from types from 'pak', since that would
# amount to testing the library when that is not
# our responsibility.

def test_angle():
    assert_type_marshal(
        types.Angle,

        (math.tau * 0 / 8, b"\x00"),
        (math.tau * 1 / 8, b"\x20"),
        (math.tau * 2 / 8, b"\x40"),
        (math.tau * 3 / 8, b"\x60"),
        (math.tau * 4 / 8, b"\x80"),
        (math.tau * 5 / 8, b"\xA0"),
        (math.tau * 6 / 8, b"\xC0"),
        (math.tau * 7 / 8, b"\xE0"),
    )

    # These must be checked outside the above call since
    # when they are marshaled back to values, they will
    # be from 0 to tau.
    assert types.Angle.pack(math.tau * 8 / 8) == b"\x00"
    assert types.Angle.pack(math.tau * 9 / 8) == b"\x20"
