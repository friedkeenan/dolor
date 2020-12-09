from ...types import *
from ..packet import *

class Base(ServerboundPacket, StatusPacket):
    pass

class RequestPacket(Base):
    id = 0x00

class PingPacket(Base):
    id = 0x01

    payload: Long
