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

                self.favicon = raw.get("favicon")

            def dict(self):
                ret = {
                    "version":     self.version,
                    "players":     self.players,
                    "description": self.description.dict(),
                }

                if self.favicon is not None:
                    ret["favicon"] = self.favicon

                return ret

            def __repr__(self):
                return f"{type(self).__name__}({self.dict()})"

        # TODO: Default?

        @classmethod
        def _unpack(cls, buf, *, ctx=None):
            return cls.Response(Json.unpack(buf, ctx=ctx))

        @classmethod
        def _pack(cls, value, *, ctx=None):
            return Json.pack(value.dict(), ctx=ctx)

    id = 0x00

    response: Response

class PongPacket(Base):
    id = 0x01

    payload: Long
