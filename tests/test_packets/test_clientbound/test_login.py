import uuid

from dolor import *

from ...util import assert_packet_marshal_func

test_disconnect_login = assert_packet_marshal_func(
    (clientbound.DisconnectLoginPacket(reason="test"), b'\x00\x0F{"text":"test"}')
)

test_encryption_request = assert_packet_marshal_func(
    (
        clientbound.EncryptionRequestPacket(
            server_id    = "",
            public_key   = b"public_key_data",
            verify_token = b"verify_token_data",
        ),

        b"\x01\x00\x0Fpublic_key_data\x11verify_token_data",
    ),
)

test_login_success = assert_packet_marshal_func(
    (
        clientbound.LoginSuccessPacket(uuid=uuid.UUID(int=0), username="test"),

        b"\x02\x2400000000-0000-0000-0000-000000000000\x04test",
    ),
)

test_set_compression = assert_packet_marshal_func(
    (
        clientbound.SetCompressionPacket(threshold=256),

        b"\x03\x80\x02",
    )
)
