import pak

from dolor import *

def test_packet_context():
    ctx = Packet.Context("1.12.2")

    assert ctx == Packet.Context(340)

    assert hash(ctx) == hash(Packet.Context("1.12.2"))

    # Test that you can default construct 'Packet.Context'.
    Packet.Context()

def test_packet():
    class TestPacket(Packet):
        id = 1

        attr: types.String

    # Don't use 'pak.test.packet_behavior' to
    # make sure packing IDs work as expected.
    assert TestPacket(attr="test").pack() == b"\x01\x04test"
    assert TestPacket.unpack(b"\x04test") == TestPacket(attr="test")

    pak.test.packet_behavior(
        (TestPacket(attr="test"), b"\x01\x04test"),
    )

    class TestLargeID(Packet):
        id = 2**7

        attr: types.String

    pak.test.packet_behavior(
        (TestLargeID(attr="test"), b"\x80\x01\x04test"),
    )

def test_generic_packet():
    generic_cls = GenericPacketWithID(1)

    # Test caching
    assert GenericPacketWithID(1) is generic_cls

    pak.test.packet_behavior(
        (generic_cls(data=b"test"), b"\x01test"),
    )
