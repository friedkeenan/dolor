import pak

from dolor import *

def test_version_switched():
    # TODO: Add more versions once we support more than one.

    switched_type = pak.Type({
        "1.12.2": types.VarInt,
    })

    assert issubclass(switched_type, types.VersionSwitchedType)

    ctx = pak.TypeContext(ctx=PacketContext("1.12.2"))

    pak.test.type_behavior(
        switched_type,

        (0,        b"\x00"),
        (1,        b"\x01"),
        (2**7 - 1, b"\x7f"),
        (2**7,     b"\x80\x01"),

        static_size = None,
        default     = 0,
        ctx         = ctx,
    )

    static_size_switched_type = pak.Type({
        "1.12.2": types.UnsignedByte,
    })

    pak.test.type_behavior(
        static_size_switched_type,

        (0, b"\x00"),

        static_size = 1,
        default     = 0,
        ctx         = ctx,
    )

def test_typelike_values():
    switched_type = pak.Type({
        # A value of 'None' should be transformed into 'pak.EmptyType'.
        "1.12.2": None,
    })

    ctx = pak.TypeContext(ctx=PacketContext("1.12.2"))

    pak.test.type_behavior(
        switched_type,

        (None, b""),

        static_size = 0,
        default     = None,
        ctx         = ctx,
    )
