"""The foundation for class:`Packets <.Packet>`."""

import pak

from .. import types
from ..versions import Version

__all__ = [
    "PacketContext",
    "Packet",
    "GenericPacket",
    "GenericPacketWithID",
    "ServerboundPacket",
    "ClientboundPacket",
    "HandshakingPacket",
    "StatusPacket",
    "LoginPacket",
    "PlayPacket",
]

class PacketContext(pak.PacketContext):
    """The context for a :class:`Packet`.

    Parameters
    ----------
    version : versionlike
        The :class:`~.Version` the :class:`Packet` is for.
    """

    def __init__(self, version):
        self.version = Version(version)

class Packet(pak.Packet):
    """A Minecraft packet."""

    _id_type = types.VarInt

class GenericPacket(Packet):
    """A generic Minecraft packet."""

    data: pak.RawByte[None]

@pak.util.cache
def GenericPacketWithID(id):
    """Generates a subclass of :class:`GenericPacket` with the specified ID.

    .. note::

        This function is cached so that calling it with the same ID
        will yield types with the same object identity.

    Parameters
    ----------
    id : :class:`int`
        The ID of the generated :class:`GenericPacket`.

    Returns
    -------
    subclass of :class:`GenericPacket`
        The generated :class:`GenericPacket`.
    """

    return type(f"GenericPacket(0x{id:X})", (GenericPacket,), dict(
        id = id,
    ))

class ServerboundPacket(Packet):
    """A serverbound :class:`Packet`.

    :class:`Packets <Packet>` which are sent to the server should inherit
    from :class:`ServerboundPacket` to be registered as such.
    """

class ClientboundPacket(Packet):
    """A clientbound :class:`Packet`.

    :class:`Packets <Packet>` which are sent to the client should inherit
    from :class:`ClientboundPacket` to be registered as such.
    """

class HandshakingPacket(Packet):
    """A packet in the "Handshaking" state of the protocol.

    :class:`Packets <Packet>` which are in the "Handshaking" state should
    inherit from :class:`HandshakingPacket` to be registered as such.
    """

class StatusPacket(Packet):
    """A packet in the "Status" state of the protocol.

    :class:`Packets <Packet>` which are in the "Status" state should
    inherit from :class:`StatusPacket` to be registered as such.
    """

class LoginPacket(Packet):
    """A packet in the "Login" state of the protocol.

    :class:`Packets <Packet>` which are in the "Login" state should
    inherit from :class:`LoginPacket` to be registered as such.
    """

class PlayPacket(Packet):
    """A packet in the "Play" state of the protocol.

    :class:`Packets <Packet>` which are in the "Play" state should
    inherit from :class:`PlayPacket` to be registered as such.
    """
