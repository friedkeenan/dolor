import pak

from dolor import *

test_chat_message = pak.test.packet_behavior_func(
    (
        serverbound.ChatMessagePacket(message="test"),

        b"\x02\x04test",
    ),
)

test_keep_alive = pak.test.packet_behavior_func(
    (
        serverbound.KeepAlivePacket(keep_alive_id=0x69),

        b"\x0B\x00\x00\x00\x00\x00\x00\x00\x69",
    ),
)
