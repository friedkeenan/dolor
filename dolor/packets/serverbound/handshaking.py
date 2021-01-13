from ... import enums
from ...types import *
from ..packet import *

class HandshakePacket(ServerboundPacket, HandshakingPacket):
    id = 0x00

    proto_version:  VarInt
    server_address: String(255)
    server_port:    UnsignedShort
    next_state:     Enum(VarInt,  enums.State)
