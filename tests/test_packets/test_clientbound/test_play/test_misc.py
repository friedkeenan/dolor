import pak

from dolor import *

test_chat_message = pak.test.packet_behavior_func(
    (
        clientbound.ChatMessagePacket(message="test", position=enums.ChatPosition.GameInfo),

        b'\x0F\x0F{"text":"test"}\x02',
    ),
)

test_disconnect_play = pak.test.packet_behavior_func(
    (clientbound.DisconnectPlayPacket(reason="test"), b'\x1A\x0F{"text":"test"}')
)

test_keep_alive = pak.test.packet_behavior_func(
    (
        clientbound.KeepAlivePacket(keep_alive_id=0x69),

        b"\x1F\x00\x00\x00\x00\x00\x00\x00\x69",
    ),
)

test_join_game = pak.test.packet_behavior_func(
    (
        clientbound.JoinGamePacket(
            entity_id = 1,
            game_mode = enums.GameMode.Survival,
            dimension = enums.Dimension.End,
            difficulty = enums.Difficulty.Normal,
            max_players = 3,
            level_type = enums.LevelType.Default,
            reduced_debug_info = False,
        ),

        b"\x23\x00\x00\x00\x01\x00\x00\x00\x00\x01\x02\x03\x07default\x00",
    ),
)
