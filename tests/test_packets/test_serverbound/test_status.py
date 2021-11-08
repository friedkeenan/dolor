from dolor import *

from ...util import assert_packet_marshal_func

test_request = assert_packet_marshal_func(
    (serverbound.RequestPacket(), b"\x00"),
)

test_ping = assert_packet_marshal_func(
    (serverbound.PingPacket(payload=1), b"\x01\x00\x00\x00\x00\x00\x00\x00\x01"),
)
