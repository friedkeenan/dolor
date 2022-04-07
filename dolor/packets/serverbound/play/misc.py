r"""Miscellaneous :class:`~.Packet`\s."""

from ...packet import ServerboundPacket, PlayPacket

from .... import types

__all__ = [
    "KeepAlivePacket",
]

class KeepAlivePacket(ServerboundPacket, PlayPacket):
    """Sent by the :class:`~.Client` to keep the :class:`~.Connection` alive.

    When the :class:`~.Client` receives a :class:`clientbound.KeepAlivePacket <.clientbound.play.misc.KeepAlivePacket>`
    it must respond with this :class:`~.Packet` with the equivalent :attr:`keep_alive_id`
    within 20 seconds, or else it will be disconnected for timing out.
    """

    id = 0x0B

    keep_alive_id: types.Long
