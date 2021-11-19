from dolor import *

from ...util import assert_packet_marshal_func

test_login_start = assert_packet_marshal_func(
    (
        serverbound.LoginStartPacket(name="test"),

        b"\x00\x04test",
    ),
)

test_encryption_response = assert_packet_marshal_func(
    (
        serverbound.EncryptionResponsePacket(
            encrypted_shared_secret = b"shared_secret_data",
            encrypted_verify_token  = b"verify_token_data",
        ),

        b"\x01\x12shared_secret_data\x11verify_token_data",
    ),
)