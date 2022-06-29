import pak

from dolor import *

test_request = pak.test.packet_behavior_func(
    (serverbound.RequestPacket(), b"\x00"),
)

test_ping = pak.test.packet_behavior_func(
    (serverbound.PingPacket(payload=1), b"\x01\x00\x00\x00\x00\x00\x00\x00\x01"),
)
