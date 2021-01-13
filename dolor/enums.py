"""Useful enums, mostly for packets."""

import enum

from . import util

class State(enum.Enum):
    """The state used for packets.

    Also used in :class:`~.HandshakePacket`.
    """

    Handshaking = 0
    Status      = 1
    Login       = 2
    Play        = 3

class ChatPosition(enum.Enum):
    """The position of a :class:`~dolor.packets.clientbound.play.misc.ChatMessagePacket`."""

    Chat     = 0
    System   = 1
    GameInfo = 2

class Action(enum.Enum):
    """The action of a :class:`~.ClientStatusPacket`."""

    Respawn      = 0
    RequestStats = 1

class GameMode(enum.Enum):
    """A player's gamemode.

    The `Hardcore*` enums are only used in older versions.

    Used in :class:`~.JoinGamePacket` and :class:`~.RespawnPacket`.
    """

    Survival  = 0
    Creative  = 1
    Adventure = 2
    Spectator = 3

    # Hardcore flag is bit 3, only used in older versions
    HardcoreSurvival  = util.bit(3) | Survival
    HardcoreCreative  = util.bit(3) | Creative
    HardcoreAdventure = util.bit(3) | Adventure
    HardcoreSpectator = util.bit(3) | Spectator

    Invalid = 255

class LegacyDimension(enum.Enum):
    """A dimension. Only used in older versions."""

    Overworld =  0
    Nether    = -1
    End       =  1

class LevelType(enum.Enum):
    """The level type of a world. Only used in older versions."""

    Default     = "default"
    Flat        = "flat"
    LargeBiomes = "largeBiomes"
    Amplified   = "amplified"
    Customized  = "customized"
    Buffet      = "buffet"
    Default_1_1 = "default_1_1"
