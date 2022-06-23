r"""The foundation for Minecraft :class:`~.Packet`\s."""

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

    class Header(pak.Packet.Header):
        # Theoretically we could have more fields
        # in the header, and it would be "fine".
        # However, for Minecraft's protocol, I find
        # that conceptually the packet header only
        # contains the ID of the packet. Additionally
        # this makes testing packet marshaling easier.
        # May be something to consider more in the future.

        id: types.VarInt

class GenericPacket(Packet):
    """A generic Minecraft :class:`Packet`."""

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
    r"""A serverbound :class:`Packet`.

    :class:`Packet`\s which are sent to the server should inherit
    from :class:`ServerboundPacket` to be registered as such.
    """

class ClientboundPacket(Packet):
    r"""A clientbound :class:`Packet`.

    :class:`Packet`\s which are sent to the client should inherit
    from :class:`ClientboundPacket` to be registered as such.
    """

class HandshakingPacket(Packet):
    r"""A packet in the :attr:`.ConnectionState.Handshaking` state of the protocol.

    :class:`Packet`\s which are in the "Handshaking" state should
    inherit from :class:`HandshakingPacket` to be registered as such.
    """

class StatusPacket(Packet):
    r"""A packet in the :attr:`.ConnectionState.Status` state of the protocol.

    :class:`Packet`\s which are in the "Status" state should
    inherit from :class:`StatusPacket` to be registered as such.
    """

class LoginPacket(Packet):
    r"""A packet in the :attr:`.ConnectionState.Login` state of the protocol.

    :class:`Packet`\s which are in the "Login" state should
    inherit from :class:`LoginPacket` to be registered as such.
    """

class PlayPacket(Packet):
    r"""A packet in the :attr:`.ConnectionState.Play` state of the protocol.

    :class:`Packet`\s which are in the "Play" state should
    inherit from :class:`PlayPacket` to be registered as such.
    """

# TODO: Should this be in the 'enums' module?
class ConnectionState(enum.Enum):
    r"""The state of a :class:`~.Connection`.

    The state of a :class:`~.Connection` determines which
    :class:`Packte`\s it may send and receive.
    """

    Handshaking = 0
    Status      = 1
    Login       = 2
    Play        = 3

    @property
    def packet_base_class(self):
        r"""The corresponding base class for :class:`Packet`\s in the :class:`ConnectionState`."""

        # TODO: When Python 3.9 support is dropped, rewrite as a match statement.
        return {
            self.Handshaking: HandshakingPacket,
            self.Status:      StatusPacket,
            self.Login:       LoginPacket,
            self.Play:        PlayPacket,
        }[self]
