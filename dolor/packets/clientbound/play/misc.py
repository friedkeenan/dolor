from .... import enums
from ....versions import VersionRange
from ....types import *
from ...packet import *

class Base(ClientboundPacket, PlayPacket):
    pass

class ChatMessagePacket(Base):
    id = {
        VersionRange(None, "1.16-pre1"): 0x0f,
        VersionRange("1.16-pre1", None): 0x0e,
    }

    data:     Chat
    position: Enum(Byte, enums.ChatPosition)

    sender: {
        VersionRange(None, "20w21a"): None,
        VersionRange("20w21a", None): UUID,
    }

class DisconnectPlayPacket(Base):
    id = {
        VersionRange(None, "1.16-pre1"):     0x1b,
        VersionRange("1.16-pre1", "20w28a"): 0x1a,
        VersionRange("20w28a", None):        0x19,
    }

    reason: Chat

class KeepAlivePacket(Base):
    id = {
        VersionRange(None, "1.16-pre1"):     0x21,
        VersionRange("1.16-pre1", "20w28a"): 0x20,
        VersionRange("20w28a", None):        0x1f,
    }

    keep_alive_id: Long

class PlayerPositionAndLook(Base):
    id = {
        VersionRange(None, "1.16-pre1"):     0x36,
        VersionRange("1.16-pre1", "20w28a"): 0x35,
        VersionRange("20w28a", None):        0x34,
    }

    position: Vector(Double)
    yaw:      Float
    pitch:    Float

    relative: BitMask("Relative", UnsignedByte,
        x     = 0,
        y     = 1,
        z     = 2,
        y_rot = 3,
        x_rot = 4,
    )

    teleport_id: VarInt

class UpdateHealthPacket(Base):
    id = 0x49

    health:     Float
    food:       VarInt
    saturation: Float
