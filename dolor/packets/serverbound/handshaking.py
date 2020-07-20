from ... import enums
from ...types import *
from ..packet import *

class Base(ServerboundPacket, HandshakingPacket):
    pass

class HandshakePacket(Base):
    id = 0x00

    fields = {
        "proto_version":  VarInt,
        "server_address": String,
        "server_port":    UnsignedShort,
        "next_state":     Enum(VarInt, enums.State),
    }
