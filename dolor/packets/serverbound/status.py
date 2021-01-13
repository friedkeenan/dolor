from ...types import *
from ..packet import *

class RequestPacket(ServerboundPacket, StatusPacket):
    id = 0x00

class PingPacket(ServerboundPacket, StatusPacket):
    id = 0x01

    payload: Long
