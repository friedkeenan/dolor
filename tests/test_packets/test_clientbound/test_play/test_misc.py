from dolor import *

from ....util import assert_packet_marshal_func

test_chat_message = assert_packet_marshal_func(
    (
        clientbound.ChatMessagePacket(message="test", position=clientbound.ChatMessagePacket.Position.GameInfo),

        b'\x0F\x0F{"text":"test"}\x02',
    ),
)

test_disconnect_play = assert_packet_marshal_func(
    (clientbound.DisconnectPlayPacket(reason="test"), b'\x1A\x0F{"text":"test"}')
)

test_keep_alive = assert_packet_marshal_func(
    (
        clientbound.KeepAlivePacket(keep_alive_id=0x69),

        b"\x1F\x00\x00\x00\x00\x00\x00\x00\x69",
    ),
)
