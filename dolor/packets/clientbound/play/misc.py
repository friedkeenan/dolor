"""Miscellaneous :class:`Packets <.Packet>`."""

from ..common import DisconnectPacket

from ...packet import ClientboundPacket, PlayPacket

from .... import types

__all__ = [
    "DisconnectPlayPacket",
    "KeepAlivePacket",
]

class DisconnectPlayPacket(DisconnectPacket, ClientboundPacket, PlayPacket):
    """Alerts the :class:`~.Client` that it's been disconnected.

    Only available in the :attr:`.ConnectionState.Play` state. You should
    likely use :class:`clientbound.DisconnectPacket <.DisconnectPacket>` instead.
    """

    id = 0x1A

class KeepAlivePacket(ClientboundPacket, PlayPacket):
    """Sent to the :class:`~.Client` to keep the :class:`~.Connection` alive.

    The :class:`~.Client` must respond with a :class:`serverbound.KeepAlivePacket <.serverbound.play.misc.KeepAlivePacket>`
    with the same :attr:`keep_alive_id` as received within 20 seconds, or else
    it will be disconnected for timing out.
    """

    id = 0x1F

    keep_alive_id: types.Long
