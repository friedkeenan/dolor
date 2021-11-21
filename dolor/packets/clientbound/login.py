""":class:`Packets <.Packet>` in the :attr:`.ConnectionState.Login` state."""

import pak

from .common import DisconnectPacket

from ..packet import ClientboundPacket, LoginPacket

from ... import types

__all__ = [
    "DisconnectLoginPacket",
    "EncryptionRequestPacket",
    "LoginSuccessPacket",
    "SetCompressionPacket",
]

class DisconnectLoginPacket(DisconnectPacket, ClientboundPacket, LoginPacket):
    """Alerts the :class:`~.Client` that it's been disconnected.

    Only available in the :attr:`.ConnectionState.Login` state. You should
    likely use :class:`clientbound.DisconnectPacket <.DisconnectPacket>` instead.
    """

    id = 0x00

class EncryptionRequestPacket(ClientboundPacket, LoginPacket):
    """Sent by the :class:`~.Server` to enable encryption over the :class:`~.Connection`.

    The :class:`~.Client` should respond with a :class:`serverbound.EncryptionResponsePacket <.EncryptionResponsePacket>`,
    after which encryption is enabled for the :class:`~.Connection`.

    Encryption is not requested if the :class:`~.Server` is an "offline" :class:`~.Server`.
    """

    id = 0x01

    server_id:    types.String(20)
    public_key:   pak.RawByte[types.VarInt]
    verify_token: pak.RawByte[types.VarInt]

class LoginSuccessPacket(ClientboundPacket, LoginPacket):
    """Tells the :class:`~.Client` that logging in has succeeded.

    Once this is sent or received, the :class:`~.Connection` should
    change to the :attr:`.ConnectionState.Play` state.
    """

    id = 0x02

    uuid:     types.UUIDString
    username: types.String(16)

class SetCompressionPacket(ClientboundPacket, LoginPacket):
    """Enables :class:`~.Packet` compression."""

    id = 0x03

    threshold: types.VarInt
