from ...types import *
from ..packet import *

class Base(ServerboundPacket, LoginPacket):
    pass

class LoginStartPacket(Base):
    id = 0x00

    name: String(16)

class EncryptionResponsePacket(Base):
    id = 0x01

    shared_secret: RawByte[VarInt]
    verify_token:  RawByte[VarInt]

class LoginPluginResponsePacket(Base):
    id = 0x02

    message_id: VarInt
    data:       Optional(RawByte[None], Boolean)
