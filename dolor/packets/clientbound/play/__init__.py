from .... import enums
from ....types import *
from ...packet import *

class Base(ClientboundPacket, PlayPacket):
    pass

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

class RespawnPacket(Base):
    id = 0x39

    dimension:      NBT
    world_name:     Identifier
    hashed_seed:    Long
    game_mode:      Enum(UnsignedByte, enums.GameMode)
    prev_game_mode: Enum(UnsignedByte, enums.GameMode)
    debug:          Boolean
    flat:           Boolean
    copy_metadata:  Boolean

class UpdateHealthPacket(Base):
    id = 0x49

    health:     Float
    food:       VarInt
    saturation: Float
