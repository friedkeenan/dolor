from dolor import *

from ...util import assert_packet_marshal_func

test_handshake = assert_packet_marshal_func(
    (
        serverbound.HandshakePacket(
            protocol       = 340,
            server_address = "localhost",
            server_port    = 25565,
            next_state     = ConnectionState.Status,
        ),

        b"\x00\xD4\x02\x09localhost\x63\xDD\x01",
    ),
)