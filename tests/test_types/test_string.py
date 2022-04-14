import pak
import pytest

from dolor import *

def test_string():
    pak.test.assert_type_marshal(
        types.String,

        ("",     b"\x00"),
        ("Test", b"\x04Test"),

        ("a" * (2**7 - 1), b"\x7F"     + b"a" * (2**7 - 1)),
        ("a" * (2**7 - 0), b"\x80\x01" + b"a" * (2**7 - 0)),

        ("a" * 32767, b"\xFF\xFF\x01" + b"a" * 32767)
    )

    with pytest.raises(types.StringLengthError, match="Invalid data length"):
        invalid_data_length = 32767 * 4 + 1

        types.String.unpack(types.VarInt.pack(invalid_data_length) + b"a" * invalid_data_length)

    with pytest.raises(types.StringLengthError, match="Invalid string length"):
        invalid_string_length = 32767 + 1

        types.String.pack("a" * invalid_string_length)

def test_called_string():
    small_string = types.String(4)

    pak.test.assert_type_marshal(
        small_string,

        ("",     b"\x00"),
        ("Test", b"\x04Test")
    )

    with pytest.raises(types.StringLengthError, match="Invalid data length"):
        invalid_data_length = 4 * 4 + 1

        small_string.unpack(types.VarInt.pack(invalid_data_length) + b"a" * invalid_data_length)

    with pytest.raises(types.StringLengthError, match="Invalid string length"):
        invalid_string_length = 4 + 1

        small_string.pack("a" * invalid_string_length)

test_json = pak.test.assert_type_marshal_func(
    types.JSON,

    ({}, b"\x02{}"),

    ({"key": "value", "other key": "other value"}, b'\x29{"key":"value","other key":"other value"}'),
)

def test_structured_json():
    class TestStructured(types.StructuredJSON):
        test: int

    structured_type = TestStructured.value_type()
    assert structured_type is TestStructured.TestStructured
    assert issubclass(structured_type, util.StructuredDict)

    pak.test.assert_type_marshal(
        TestStructured,

        (structured_type(test=1), b'\x0A{"test":1}'),
    )

    class TestConversion(types.StructuredJSON):
        test: structured_type

    conversion_type = TestConversion.value_type()

    pak.test.assert_type_marshal(
        TestConversion,

        (conversion_type(test=structured_type(test=1)), b'\x13{"test":{"test":1}}'),
    )

    class TestDefault(types.StructuredJSON):
        test: int = 0

    assert TestDefault.default() == TestDefault.TestDefault(test=0)

def test_identifier():
    test_id = types.Identifier.Identifier("stone")

    assert str(test_id) == "minecraft:stone"

    assert types.Identifier.Identifier(test_id) == test_id

    pak.test.assert_type_marshal(
        types.Identifier,

        (test_id, b"\x0Fminecraft:stone")
    )

    with pytest.raises(ValueError, match="Invalid"):
        types.Identifier.Identifier("namespace:name:invalid")
