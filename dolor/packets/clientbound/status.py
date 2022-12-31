r""":class:`Packet`\s in the :attr:`.ConnectionState.Status` state."""

from ..packet import ClientboundPacket, StatusPacket

from ...versions import Version
from ... import types
from ... import util

__all__ = [
    "ResponsePacket",
    "PongPacket",
]

class ResponsePacket(ClientboundPacket, StatusPacket):
    """A reply to a :class:`serverbound.RequestPacket <.RequestPacket>`."""

    class Response(types.StructuredJSON):
        """The response data.

        See https://wiki.vg/Server_List_Ping#Response for more information.
        """

        class PlayersInfo(util.StructuredDict):
            """Info about the :class:`~.Server`'s players."""

            max:    int
            online: int
            sample: list = util.StructuredDict.UNSPECIFIED # TODO: Figure out list of 'StructuredDict's

        version:     Version
        players:     PlayersInfo
        description: types.Chat.Chat
        favicon:     str = util.StructuredDict.UNSPECIFIED

        # Seemingly non-standard information regarding the server's mods.
        modinfo: dict = util.StructuredDict.UNSPECIFIED

    id = 0x00

    response: Response

class PongPacket(ClientboundPacket, StatusPacket):
    """A reply to :class:`serverbound.PingPacket <.PingPacket>`.


    The :attr:`payload` attribute should hold the same value as the
    corresponding :class:`serverbound.PingPacket <.PingPacket>`.
    """

    id = 0x01

    payload: types.Long
