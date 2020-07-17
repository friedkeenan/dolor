from .... import enums
from ....types import *
from ...packet import *

class Base(ClientboundPacket, PlayPacket):
    pass

class ChatMessagePacket(Base):
    id = 0x0F

    fields = {
        "data":     Json, # TODO: Chat type
        "position": Byte,
    }

class DisconnectPlayPacket(Base):
    id = 0x1B

    fields = {"reason": Json} # TODO: Chat type

class KeepAlivePacket(Base):
    id = 0x21

    fields = {"id": Long}

class RespawnPacket(Base):
    id = 0x3B

    fields = {
        "dimension":   Enum(Int, enums.Dimension),
        "hashed_seed": Long,
        "game_mode":   UnsignedByte,
        "level_type":  String,
    }

class UpdateHealthPacket(Base):
    id = 0x49

    fields = {
        "health":     Float,
        "food":       VarInt,
        "saturation": Float,
    }