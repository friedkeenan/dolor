""":class:`Packets <.Packet>` in the :attr:`.ConnectionState.Handshaking` state."""

import pak

from ..packet import ServerboundPacket, HandshakingPacket, ConnectionState

from ... import types

__all__ = [
    "HandshakePacket",
]

class HandshakePacket(ServerboundPacket, HandshakingPacket):
    """Sent to begin a :class:`~.Connection`.

    The :class:`~.Server` should transition to the
    state specified by :attr:`next_state`.
    """

    id = 0x00

    protocol:       types.VarInt
    server_address: types.String(255)
    server_port:    types.UnsignedShort
    next_state:     pak.Enum(types.VarInt, ConnectionState)
