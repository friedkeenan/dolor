from dolor import *

from ..util import assert_packet_marshal

def test_packet():
    class TestPacket(Packet):
        id = 1

        attr: types.String

    # Don't use 'assert_packet_marshal' to
    # make sure packing IDs work as expected.
    assert TestPacket(attr="test").pack() == b"\x01\x04test"
    assert TestPacket.unpack(b"\x04test") == TestPacket(attr="test")

    class TestLargeID(Packet):
        id = 2**7

        attr: types.String

    assert_packet_marshal(
        (TestLargeID(attr="test"), b"\x80\x01\x04test"),
    )

def test_generic_packet():
    generic_cls = GenericPacketWithID(1)

    # Test caching
    assert GenericPacketWithID(1) is generic_cls

    assert_packet_marshal(
        (generic_cls(data=b"test"), b"\x01test"),
    )
