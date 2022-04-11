r"""Miscellaneous :class:`~.Packet`\s."""

import enum
import pak

from ..common import DisconnectPacket

from ...packet import ClientboundPacket, PlayPacket

from .... import types

__all__ = [
    "ChatMessagePacket",
    "DisconnectPlayPacket",
    "KeepAlivePacket",
]

class ChatMessagePacket(ClientboundPacket, PlayPacket):
    """A :class:`~.types.chat.Chat` message from the :class:`~.Server`.

    For messages from the :class:`~.Client`, see
    :class:`serverbound.ChatMessagePacket <.serverbound.play.misc.ChatMessagePacket>`.
    """

    class Position(enum.Enum):
        """The position of the message."""

        Chat     = 0
        System   = 1
        GameInfo = 2

    id = 0x0F

    message:  types.Chat
    position: pak.Enum(types.Byte, Position)

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
