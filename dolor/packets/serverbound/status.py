from ...types import *
from ..packet import *

class Base(ServerboundPacket, StatusPacket):
    pass

class RequestPacket(Base):
    id = 0x00
    fields = {}

class PingPacket(Base):
    id = 0x01

    fields = {"payload": Long}