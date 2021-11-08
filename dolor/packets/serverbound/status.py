""":class:`Packets <.Packet>` in the "Status" state."""

from ..packet import *

from ... import types

class RequestPacket(ServerboundPacket, StatusPacket):
    """Requests the status from the :class:`~.Server`."""

    id = 0x00

class PingPacket(ServerboundPacket, StatusPacket):
    """Pings the :class:`~.Server`.

    The :attr:`payload` attribute conventionally contains
    the current time in milliseconds so the :class:`~.Client`
    can figure out its ping to the :class:`~.Server`.
    """

    id = 0x01

    payload: types.Long
