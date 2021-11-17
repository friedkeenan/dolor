"""The foundation for :class:`Packets <.Packet>`."""

import enum
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
    "ConnectionState",
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

    def __eq__(self, other):
        if not isinstance(other, PacketContext):
            return NotImplemented

        return self.version == other.version

    def __hash__(self):
        return hash(self.version)

class Packet(pak.Packet):
    """A Minecraft packet."""

    _id_type = types.VarInt

class GenericPacket(Packet):
    """A generic Minecraft packet."""

    # NOTE: This inherits from our 'Packet' class instead of
    # 'pak.GenericPacket' so that if we add utilities to our
    # 'Packet', then they also automatically get added to our
    # 'GenericPacket'.

    data: pak.RawByte[None]

# TODO: When Python 3.7 support is dropped, make 'id' a positional-only parameter.
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

    return type(f"GenericPacketWithID(0x{id:X})", (GenericPacket,), dict(
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
    """A packet in the :attr:`.ConnectionState.Handshaking` state of the protocol.

    :class:`Packets <Packet>` which are in the "Handshaking" state should
    inherit from :class:`HandshakingPacket` to be registered as such.
    """

class StatusPacket(Packet):
    """A packet in the :attr:`.ConnectionState.Status` state of the protocol.

    :class:`Packets <Packet>` which are in the "Status" state should
    inherit from :class:`StatusPacket` to be registered as such.
    """

class LoginPacket(Packet):
    """A packet in the :attr:`.ConnectionState.Login` state of the protocol.

    :class:`Packets <Packet>` which are in the "Login" state should
    inherit from :class:`LoginPacket` to be registered as such.
    """

class PlayPacket(Packet):
    """A packet in the :attr:`.ConnectionState.Play` state of the protocol.

    :class:`Packets <Packet>` which are in the "Play" state should
    inherit from :class:`PlayPacket` to be registered as such.
    """

class ConnectionState(enum.Enum):
    """The state of a :class:`~.Connection`.

    The state of a :class:`~.Connection` determines which
    :class:`Packtes <Packet>` it may send and receive.
    """

    Handshaking = 0
    Status      = 1
    Login       = 2
    Play        = 3

    @property
    def packet_base_class(self):
        """The corresponding base class for :class:`Packets <Packet>` in the :class:`ConnectionState`."""

        return {
            self.Handshaking: HandshakingPacket,
            self.Status:      StatusPacket,
            self.Login:       LoginPacket,
            self.Play:        PlayPacket,
        }[self]
