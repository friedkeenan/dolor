from .... import enums
from ....types import *
from ...packet import *

class Base(ServerboundPacket, PlayPacket):
    pass

class ChatMessagePacket(Base):
    id = 0x03

    fields = {"message": String}

class KeepAlivePacket(Base):
    id = 0x0F

    fields = {"id": Long}

class ClientStatusPacket(Base):
    id = 0x04

    fields = {"action": Enum(VarInt, enums.Action)}