""":class:`Packets <.Packet>` in the :attr:`.ConnectionState.Login` state."""

import pak

from ..packet import ServerboundPacket, LoginPacket

from ... import types

__all__ = [
    "LoginStartPacket",
    "EncryptionResponsePacket",
]

class LoginStartPacket(ServerboundPacket, LoginPacket):
    """Sent by the :class:`~.Client` to begin logging in."""

    id = 0x00

    name: types.String(16)

class EncryptionResponsePacket(ServerboundPacket, LoginPacket):
    """Responds to a :class:`clientbound.EncryptionRequestPacket <.EncryptionRequestPacket>`.

    After this is sent to the :class:`~.Server`, encryption is enabled for the :class:`~.Connection`.
    """

    id = 0x01

    encrypted_shared_secret: pak.RawByte[types.VarInt]
    encrypted_verify_token:  pak.RawByte[types.VarInt]
