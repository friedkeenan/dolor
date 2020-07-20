from ...types import *
from ..packet import *

class Base(ServerboundPacket, LoginPacket):
    pass

class LoginStartPacket(Base):
    id = 0x00

    fields = {"name": String}

class EncryptionResponsePacket(Base):
    id = 0x01

    fields = {
        "shared_secret": RawByteArray(VarInt),
        "verify_token":  RawByteArray(VarInt),
    }

class LoginPluginResponse(Base):
    id = 0x02

    fields = {
        "message_id": VarInt,
        "successful": Boolean,
        "data":       RawByteArray(),
    }
