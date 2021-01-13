from .... import enums
from ....versions import VersionRange
from ....types import *
from ...packet import *

class ChatMessagePacket(ServerboundPacket, PlayPacket):
    id = 0x03

    message: String(256)

class ClientStatusPacket(ServerboundPacket, PlayPacket):
    id = 0x04

    action: Enum(VarInt, enums.Action)

class KeepAlivePacket(ServerboundPacket, PlayPacket):
    id = {
        VersionRange(None, "20w16a"): 0x0f,
        VersionRange("20w16a", None): 0x10,
    }

    keep_alive_id: Long
