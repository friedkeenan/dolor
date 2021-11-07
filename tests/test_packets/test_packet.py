from dolor import *

from ..util import assert_packet_marshal

def test_packet():
    class TestPacket(Packet):
        id = 1

        attr: types.String

    assert TestPacket(attr="test").pack() == b"\x01\x04test"
    assert TestPacket.unpack(b"\x04test") == TestPacket(attr="test")

    class TestLargeID(Packet):
        id = 2**7

        attr: types.String

    assert TestLargeID(attr="test").pack() == b"\x80\x01\x04test"
    assert TestLargeID.unpack(b"\x04test") == TestLargeID(attr="test")

def test_generic_packet():
    generic_cls = GenericPacketWithID(1)

    # Test caching
    assert GenericPacketWithID(1) is generic_cls

    assert generic_cls(data=b"test").pack() == b"\x01test"
    assert generic_cls.unpack(b"test") == generic_cls(data=b"test")
