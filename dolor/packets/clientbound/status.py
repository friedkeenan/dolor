from ...types import *
from ..packet import *

class Base(ClientboundPacket, StatusPacket):
    pass

class ResponsePacket(Base):
    class Response(Type):
        class Response:
            def __init__(self, raw):
                self.version = raw["version"]
                self.players = raw["players"]
                self.description = Chat.Chat(raw["description"])

                if "favicon" in raw:
                    self.favicon = raw["favicon"]
                else:
                    self.favicon = None

            def to_dict(self):
                ret = {
                    "version": self.version,
                    "players": self.players,
                    "description": self.description.to_dict(),
                }

                if self.favicon is not None:
                    ret["favicon"] = self.favicon

                return ret

            def __repr__(self):
                return f"{type(self).__name__}({repr(self.to_dict())})"

        def unpack(self, buf):
            return self.Response(Json(buf).value)

        def __bytes__(self):
            return bytes(Json(self.value.to_dict()))

    id = 0x00

    fields = {"response": Response}

class PongPacket(Base):
    id = 0x01

    fields = {"payload": Long}
