from .... import enums
from ....types import *
from ...packet import *

class Base(ClientboundPacket, PlayPacket):
    pass

GameModeType = Enum(UnsignedByte, enums.GameMode)

class ChatMessagePacket(Base):
    id = 0x0e

    data:     Chat
    position: Enum(Byte, enums.ChatPosition)
    sender:   UUID

class DisconnectPlayPacket(Base):
    id = 0x19

    reason: Chat

class KeepAlivePacket(Base):
    id = 0x1f

    keep_alive_id: Long

class JoinGamePacket(Base):
    id = 0x24

    entity_id:             Int
    hardcore:              Boolean
    game_mode:             GameModeType
    prev_game_mode:        GameModeType
    world_names:           Identifier[VarInt]
    dimension_codec:       NBT
    dimension:             NBT
    world_name:            Identifier
    hashed_seed:           Long
    max_players:           VarInt
    view_distance:         VarInt
    reduced_debug_info:    Boolean
    enable_respawn_screen: Boolean
    debug:                 Boolean
    flat:                  Boolean

class RespawnPacket(Base):
    id = 0x39

    dimension:      NBT
    world_name:     Identifier
    hashed_seed:    Long
    game_mode:      GameModeType
    prev_game_mode: GameModeType
    debug:          Boolean
    flat:           Boolean
    copy_metadata:  Boolean

class UpdateHealthPacket(Base):
    id = 0x49

    health:     Float
    food:       VarInt
    saturation: Float
