from ...versions import VersionRange
from ...types import *
from ..packet import *

class Base(ClientboundPacket, LoginPacket):
    pass

class DisconnectLoginPacket(Base):
    id = 0x00

    reason: Chat

class EncryptionRequestPacket(Base):
    id = 0x01

    server_id:    String(20)
    public_key:   RawByte[VarInt]
    verify_token: RawByte[VarInt]

class LoginSuccessPacket(Base):
    id = 0x02

    uuid: {
        VersionRange(None, "20w13a"): UUIDString,
        VersionRange("20w13a", None): UUID,
    }

    username: String(16)

class SetCompressionPacket(Base):
    id = 0x03

    threshold: VarInt

class LoginPluginRequestPacket(Base):
    id = 0x04

    message_id: VarInt
    channel:    Identifier
    data:       RawByte[None]
