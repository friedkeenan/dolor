from ...types import *
from ..packet import *

class Base(ClientboundPacket, LoginPacket):
    pass

class DisconnectStatusPacket(Base):
    id = 0x00

    fields = {"reason": Chat}

class EncryptionRequestPacket(Base):
    id = 0x01

    fields = {
        "server_id":    String,
        "pub_key":      RawByteArray(VarInt),
        "verify_token": RawByteArray(VarInt),
    }

class LoginSuccessPacket(Base):
    id = 0x02

    fields = {
        "uuid":     UUIDString,
        "username": String,
    }

class SetCompressionPacket(Base):
    id = 0x03

    fields = {"threshold": VarInt}

class LoginPluginRequestPacket(Base):
    id = 0x04

    fields = {
        "message_id": VarInt,
        "channel":    Identifier,
        "data":       RawByteArray(),
    }
