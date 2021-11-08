from dolor import *

from ...util import assert_packet_marshal_func

Response = clientbound.ResponsePacket.Response

test_response = assert_packet_marshal_func(
    (
        clientbound.ResponsePacket(
            response = Response.Response(
                version = Version("1.12.2"),

                players = Response.PlayersInfo(
                    max    = 20,
                    online = 1,
                    sample = [],
                ),

                description = {}, # TODO: Chat

                favicon = "data:image/png;base64,VGVzdA==",
            )
        ),

        b'\x00\x94\x01{"version":{"name":"1.12.2","protocol":340},"players":{"max":20,"online":1,"sample":[]},"description":{},"favicon":"data:image/png;base64,VGVzdA=="}'
    ),

    (
        clientbound.ResponsePacket(
            response = Response.Response(
                version = Version("1.12.2"),

                players = Response.PlayersInfo(
                    max    = 20,
                    online = 1,
                    sample = [],
                ),

                description = {}, # TODO: Chat

                # Missing favicon
            )
        ),

        b'\x00\x69{"version":{"name":"1.12.2","protocol":340},"players":{"max":20,"online":1,"sample":[]},"description":{}}'
    ),
)

test_pong = assert_packet_marshal_func(
    (clientbound.PongPacket(payload=1), b"\x01\x00\x00\x00\x00\x00\x00\x00\x01"),
)
