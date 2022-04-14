import pak

from dolor import *

test_request = pak.test.assert_packet_marshal_func(
    (serverbound.RequestPacket(), b"\x00"),
)

test_ping = pak.test.assert_packet_marshal_func(
    (serverbound.PingPacket(payload=1), b"\x01\x00\x00\x00\x00\x00\x00\x00\x01"),
)
