from dolor import *

from ....util import assert_packet_marshal_func

test_chat_message = assert_packet_marshal_func(
    (
        serverbound.ChatMessagePacket(message="test"),

        b"\x02\x04test",
    ),
)

test_keep_alive = assert_packet_marshal_func(
    (
        serverbound.KeepAlivePacket(keep_alive_id=0x69),

        b"\x0B\x00\x00\x00\x00\x00\x00\x00\x69",
    ),
)
