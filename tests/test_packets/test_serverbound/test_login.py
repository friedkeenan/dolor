import pak

from dolor import *

test_login_start = pak.test.packet_behavior_func(
    (
        serverbound.LoginStartPacket(name="test"),

        b"\x00\x04test",
    ),
)

test_encryption_response = pak.test.packet_behavior_func(
    (
        serverbound.EncryptionResponsePacket(
            encrypted_shared_secret = b"shared_secret_data",
            encrypted_verify_token  = b"verify_token_data",
        ),

        b"\x01\x12shared_secret_data\x11verify_token_data",
    ),
)
