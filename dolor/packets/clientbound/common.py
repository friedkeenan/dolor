r""":class:`~.Packet` types common between :class:`~.ConnectionState`\s."""

from ..packet import Packet

from ... import types

__all__ = [
    "DisconnectPacket",
]

class DisconnectPacket(Packet):
    """Alerts the :class:`~.Client` that it's been disconnected.

    Has no ID of its own, but is the parent class of
    :class:`clientbound.DisconnectLoginPacket <.DisconnectLoginPacket>`
    and :class:`clientbound.DisconnectPlayPacket <.DisconnectPlayPacket>`.
    """

    reason: types.Chat
