from .... import enums
from ....types import *
from ...packet import *

class Base(ServerboundPacket, PlayPacket):
    pass

class ChatMessagePacket(Base):
    id = 0x03

    message: String

class ClientStatusPacket(Base):
    id = 0x04

    action: Enum(VarInt, enums.Action)

class KeepAlivePacket(Base):
    id = 0x10

    keep_alive_id: Long
