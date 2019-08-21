from ...types import *
from ..packet import *

class Base(ClientboundPacket, StatusPacket):
    pass

class ResponsePacket(Base):
    id = 0x00

    fields = [{"response": Json}]

class PongPacket(Base):
    id = 0x01

    fields = [{"payload": Long}]