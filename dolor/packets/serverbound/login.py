from ...types import *
from ..packet import *

class LoginStartPacket(ServerboundPacket, LoginPacket):
    id = 0x00

    name: String(16)

class EncryptionResponsePacket(ServerboundPacket, LoginPacket):
    id = 0x01

    shared_secret: RawByte[VarInt]
    verify_token:  RawByte[VarInt]

class LoginPluginResponsePacket(ServerboundPacket, LoginPacket):
    id = 0x02

    message_id: VarInt
    data:       Optional(RawByte[None], Boolean)
