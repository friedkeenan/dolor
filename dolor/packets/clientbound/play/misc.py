r"""Miscellaneous :class:`~.Packet`\s."""

import enum
import pak

from ..common import DisconnectPacket

from ...packet import ClientboundPacket, PlayPacket

from .... import types
from .... import enums

__all__ = [
    "ChatMessagePacket",
    "DisconnectPlayPacket",
    "KeepAlivePacket",
    "JoinGamePacket",
]

class ChatMessagePacket(ClientboundPacket, PlayPacket):
    """A :class:`~.Chat.Chat` message from the :class:`~.Server`.

    For messages from the :class:`~.Client`, see
    :class:`serverbound.ChatMessagePacket <.serverbound.play.misc.ChatMessagePacket>`.
    """

    id = 0x0F

    message:  types.Chat
    position: pak.Enum(types.Byte, enums.ChatPosition)

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

class JoinGamePacket(ClientboundPacket, PlayPacket):
    """Sent to the :class:`~.Client` shortly after successfully logging in."""

    id = 0x23

    entity_id:          types.Int
    game_mode:          pak.Enum(types.UnsignedByte, enums.GameMode)
    dimension:          pak.Enum(types.Int,          enums.Dimension)
    difficulty:         pak.Enum(types.UnsignedByte, enums.Difficulty)
    max_players:        types.UnsignedByte
    level_type:         pak.Enum(types.String(16),   enums.LevelType)
    reduced_debug_info: types.Boolean
