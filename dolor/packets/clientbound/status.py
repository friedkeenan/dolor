from ...versions import Version
from ...types import *
from ..packet import *

class ResponsePacket(ClientboundPacket, StatusPacket):
    class Response(Type):
        class Response:
            def __init__(self, *, version=None, players=None, description=None, favicon=None, raw=None):
                if raw is not None:
                    self.version = Version(raw["version"]["name"], raw["version"]["protocol"])
                    self.players = raw["players"]

                    self.description = Chat.Chat(raw["description"])

                    self.favicon = raw.get("favicon")
                else:
                    if not isinstance(description, Chat.Chat):
                        description = Chat.Chat(description)

                    self.version     = version
                    self.players     = players
                    self.description = description
                    self.favicon     = favicon

            def dict(self):
                ret = {
                    "version": {
                        "name":     self.version.name,
                        "protocol": self.version.proto
                    },

                    "players":     self.players,
                    "description": self.description.dict(),
                }

                if self.favicon is not None:
                    ret["favicon"] = self.favicon

                return ret

            def __repr__(self):
                return f"{type(self).__name__}({self.dict()})"

        _default = Response()

        @classmethod
        def _unpack(cls, buf, *, ctx=None):
            return cls.Response(raw=Json.unpack(buf, ctx=ctx))

        @classmethod
        def _pack(cls, value, *, ctx=None):
            return Json.pack(value.dict(), ctx=ctx)

    id = 0x00

    response: Response

class PongPacket(ClientboundPacket, StatusPacket):
    id = 0x01

    payload: Long
